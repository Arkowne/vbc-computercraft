local bmi = require("bmi")  -- sans le ".lua"

local args = { ... }

-- === Mode DEBUG ===
local debug = true

-- Initialise DFPWM
local dfpwm = require("cc.audio.dfpwm")
local decoder = dfpwm.make_decoder()

function errorHandler(type, data)

    if type == "cantDownloadAudio" then
        if urlExists(data) then
            error("Can't download audio : Unknown error.")
        else
            error("Can't download audio : can't reach the server.")
        end
    elseif type == "errorWhileDownloading" then
        if urlExists(data) then
            error("Can't download file ".. data .. ": Unknown error.")
        else
            error("Can't download file ".. data .. ": can't reach the server.")
        end
    elseif type == "errorOpeningFile" then
        error("Error while opening " .. data)
    elseif type == "missingUrl" then
        error("Can't download file, missing url.")
    elseif type == "cantReachServer" then
        error("Can't reach the server.")
    elseif type == "invalidServerResponse" then
        error("Invalid server response : ", data)
    elseif type == "invalidUrl" then
        error("Invalid URL : ", data)
    end
end

local function checksum(path)
    if not fs.exists(path) then error("Fichier introuvable : "..path) end
    local h = fs.open(path, "rb")
    local sum = 0
    repeat
        local chunk = h.read(1024)
        if chunk then
            for i = 1, #chunk do
                sum = (sum + chunk:byte(i)) % 2^32
            end
        end
    until not chunk
    h.close()
    return sum
end

function downloadAndInspect(url, destPath)
    -- 1) Ouvrir la requÃÂªte HTTP
    local resp = http.get(url)
    if not resp then
        return false, "ÃÂchec du tÃÂ©lÃÂ©chargement", nil, nil
    end

    -- 2) Lire lÃ¢ÂÂenÃ¢ÂÂtÃÂªte Content-Length (nil si absent)
    local headers  = resp.getResponseHeaders()
    local declared = headers and tonumber(headers["Content-Length"])

    -- 3) Lire tout le contenu
    local data = resp.readAll()
    resp.close()

    -- 4) Sauvegarder sur le disque
    local f = fs.open(destPath, "wb")
    f.write(data)
    f.close()

    -- 5) Mesurer la taille rÃÂ©elle
    local actualSize = fs.getSize(destPath)

    -- 6) VÃÂ©rifier cohÃÂ©rence taille annoncÃÂ©e / rÃÂ©elle
    if declared and declared ~= actualSize then
        -- avertissement, mais on continue pour le checksum
        print(("Ã¢ÂÂ Ã¯Â¸Â Taille dÃÂ©clarÃÂ©e (%d) != taille rÃÂ©elle (%d)"):format(declared, actualSize))
    end

    -- 7) Calculer le checksum
    local actualSum = checksum(destPath)

    return true,
           "TÃÂ©lÃÂ©chargement et inspection terminÃÂ©s",
           actualSize,
           actualSum
end

function dl_audio(url)
    local path = "audio.dfpwm"
    print( "URL : " .. url)

    local ok, msg, size, sum = downloadAndInspect(url, path)
    if ok then
        print(("SuccÃÂ¨sÃ¢ÂÂ¯: taille = %d octets, checksum = %u"):format(size, sum))
        return "succes"
    else
        print("ErreurÃ¢ÂÂ¯: "..msg)
        return "error"
    end
end

local function dl_image(url, fileName)
    local resp = http.get(url)
    if not resp then
        errorHandler("errorWhileDownloading", url)
        return false
    end
    local file = fs.open(fileName, "w")
    file.write(resp.readAll())
    file.close()
    resp.close()
    return true
end

local function load_metadata()
    dl_image(adress .. "/videos/" .. id .. "/metadata.txt", "temp/metadata.txt")
    local file = fs.open("temp/metadata.txt", "r")
    if not file then
        error("Impossible d'ouvrir metadata.txt")
        errorHandler("errorOpeningFile", "temp/metadata.txt")
    end
    local content = file.readAll()
    file.close()

    local fps = tonumber(content:match("fps=(%d+)"))
    local frames = tonumber(content:match("frames=(%d+)"))
    print("FPS :", fps)
    print("Nombre de frames :", frames)
    return fps, frames
end

function urlExists(url)
    local ok, response = pcall(http.get, url)
    if not ok or not response then
        return false
    end

    local code = response.getResponseCode and response.getResponseCode() or 200
    response.close()
    return code >= 200 and code < 400
end

function file_exists(path)
    local file = io.open(path, "r")
    if file then
        file:close()
        return true
    else
        return false
    end
end


function blockUntilSignal();
    -- Bloque le programme tant qu'il n'y a pas de signal de redstone sous le PC
    local side = "bottom"  -- côté à vérifier ("bottom", "top", "left", etc.)

    print("En attente du signal de redstone sous le PC...")

    -- Boucle infinie tant qu'il n'y a pas de signal
    while not redstone.getInput(side) do
        sleep(0.1)  -- évite de saturer le CPU
    end

    print("Signal détecté ! Le programme peut continuer.")
    -- Ici tu peux mettre le reste de ton programme
end

function downloadVideo(serverip, url, width, height)
    if not url then
        errorHandler("missingUrl")
    end

    -- Préparer le corps JSON
    local body = { url = url }
    if width then body.width = width end
    if height then body.height = height end
    local jsonBody = textutils.serializeJSON(body)

    -- Envoyer la requête POST au serveur Python
    local response = http.post(serverip, jsonBody, {
        ["Content-Type"] = "application/json"
    })

    if not response then
        errorHandler("cantReachServer")
    end

    -- Lire la réponse JSON
    local responseBody = response.readAll()
    response.close()

    local data = textutils.unserializeJSON(responseBody)
    if not data or not data.id then
        errorHandler("invalidServerResponse", tostring(responseBody))
    end

    -- Retourner l'ID généré immédiatement
    return data.id
end

function loadAudio()
    local h = fs.open("audio.dfpwm", "rb")
    if not h then return {} end
    local raw = h.readAll()
    h.close()
    local chunks, size = {}, 16 * 1024
    for i = 1, #raw, size do
        chunks[#chunks + 1] = raw:sub(i, i + size - 1)
    end
    return chunks
end


function playAudio()
    startTimeSound = os.clock()
    audioElapsed = 0

    if isSpeaker == false then return end

    local subChunkSize = 1024
    local ci, offset = 1, 1
    local running = true

    local function audioThread()
        while programRunning and ci <= #chunks do
            if not isPlaying then
                speaker.stop()
                os.pullEvent()  -- attend n'importe quel event avant de reprendre
            else
                local c = chunks[ci]
                if c then
                    if offset > #c then
                        ci = ci + 1
                        offset = 1
                    else
                        local subChunk = c:sub(offset, offset + subChunkSize - 1)
                        local pcm = decoder(subChunk)
                        -- Attendre que le speaker ait de la place
                        while not speaker.playAudio(pcm) do
                            os.pullEvent("speaker_audio_empty")
                        end
                        offset = offset + subChunkSize
                    end
                else
                    ci = ci + 1
                end
            end
        end
        running = false
    end

    local function timerThread()
        while running do
            if isPlaying then
                audioElapsed = os.clock() - startTimeSound
            end
            sleep(0.05)
        end
    end

    -- Lancer le flux audio et la mise à jour du timer en parallèle
    parallel.waitForAny(audioThread, timerThread)
end


function playVideo()
    local i = 0
    local frameInterval = 1 / fps
    local lastTime = os.clock()
    elapsed = 0  -- ✅ Toujours défini dès le début

    -- Tant que le programme tourne et qu'il reste des frames
    while i < frames and programRunning do
        local currentTime = os.clock()
        local dt = currentTime - lastTime
        lastTime = currentTime

        -- Pause globale
        while not isPlaying do
            os.pullEvent()
            lastTime = os.clock()  -- Reset le timer pour éviter que le temps continue pendant la pause
        end

        -- ✅ Incrémente seulement si on est en lecture
        elapsed = elapsed + dt

        -- Calcul de la frame attendue selon le temps écoulé
        local expectedFrame = math.floor(elapsed * fps)

        -- Corrige si la vidéo est en retard (optionnel)
        if expectedFrame > i then
            i = expectedFrame
        end

        if i >= frames then break end

        local index = string.format("%05d", i)
        local url = adress .. "/videos/" .. id .. "/frame_" .. index .. ".bmi"
        local path = "temp/frame_" .. index .. ".bmi"

        -- Télécharge et affiche la frame
        if dl_image(url, path) and file_exists(path) then
            bmi.draw(path, {term = videoscreen})
            fs.delete(path)
        end

        -- Affichage debug (optionnel)
        if args[3] == "debug" then
            local debugText = string.format(
                "Frame: %d/%d | Temps: %.2fs | Sync: %.3fs",
                i, frames, elapsed, i / fps - elapsed
            )
            videoscreen.setCursorPos(1, h)
            videoscreen.setTextColor(colors.white)
            videoscreen.clearLine()
            write(debugText)
        end

        -- Avance à la frame suivante
        i = i + 1

        -- Synchronise avec le temps réel de lecture
        local nextFrameTime = i / fps
        local delay = nextFrameTime - elapsed
        if delay > 0 then sleep(delay) end

        drawTimer()

        -- Interface terminal (si pas d’écran externe)
        if not isExternalMonitor then
            local width, height = term.getSize()
            term.setBackgroundColor(colors.orange)
            term.setTextColor(colors.black)
            term.setCursorPos(1, height - 2)
            term.write(isPlaying and "Pause " or "Start ")
            term.setCursorPos(1, height - 1)
            term.write("Stop ")
            term.setCursorPos(1, height)
            term.write(formatTime(elapsed))
        end
    end

    programRunning = false
    endSession()
end





-- Recuperationd de l'adress du serveur
adress = settings.get("vbc.ip_server", true)
fs.makeDir("temp")
programRunning = true


-- VÃ©rification des arguments
local command = args[1]
if command == "play" then
    id = args[2]
    if not id then
        print("\nVeuillez renseigner l'ID de votre vidéo.")
        print("Commande : vbc <id>")
        print("")
        os.pullEvent()
        return
    else
        --print(adress .. "/videos/" .. args[2] .. "/lock.txt")
        if not urlExists(adress .. "/videos/" .. args[2] .. "/lock.txt") then
            print("The video is not avaiable or not fully generated.")
            return
        end
    end


elseif command == "download" then
    vid_adress = args[2]
    if not vid_adress:match("^https?://") then
        error("invalidUrl", vid_adress)
    end

else
    print("Veuillez entrer une commande valide. ")

end



-- Trouve le moniteur et le configure

-- Trying to find external monitor
local monitor = peripheral.find("monitor")
isExternalMonitor = false
if monitor then
    videoscreen = monitor
    videoscreen.setTextScale(0.5)
    videoscreen.clear()
    print("Screen connected")
    isExternalMonitor = true
else
    -- Sinon, on fait autre chose
    videoscreen = term
    print("No external screen found.")
    -- Par exemple afficher un message dans la console du computer
end

local swidth, sheight = videoscreen.getSize()



isSpeaker = false
if args[3] ~= "no" and command == "play" then
    speaker = peripheral.find("speaker")
    if not speaker then
        error("Can't find speaker")
    else
        print("Speaker found !")
        isSpeaker = True
    end
end





-- Telecharge l'audio
if isSpeaker ~= false and command == "play" then
    state = dl_audio(adress .. "/videos/" .. id .. "/audio.dfpwm")
    if state == "error" then
        errorHandler("cantDownloadAudio", adress .. "/videos/" .. id .. "/audio.dfpwm")
    else
        print("Audio telecharge.")
    end
end

function endSession()
    videoscreen.setBackgroundColor(colors.black)
    videoscreen.clear()
    term.setBackgroundColour(colors.black)
    term.clear()
    drawFrame(term)
    term.setCursorPos(3, 3)
    term.setBackgroundColor(colors.orange)
    term.setTextColor(colors.white)
    term.write("Video ended : click to close")
    term.setBackgroundColor(colors.black)
    term.setCursorPos(1,1)
    os.pullEvent("mouse_click")
    term.clear()
    
end

function formatTime(seconds)
    local h = math.floor(seconds / 3600)
    local m = math.floor((seconds % 3600) / 60)
    local s = math.floor(seconds % 60)
    -- Format avec des zéros devant si nécessaire
    return string.format("%02d:%02d:%02d", h, m, s)
end

function drawFrame(s)
    -- Couleur orange (à approximativement en ComputerCraft)
    local orange = colors.orange or colors.orange or 0xFF8000 -- fallback si non défini
    
    local largeur, hauteur = s.getSize()
    
    s.setBackgroundColor(orange)
    s.setCursorPos(1,1)
    -- Dessiner les lignes horizontales du cadre
    paintutils.drawLine(1, 1, largeur, 1, colors.orange)
    paintutils.drawLine(1, 1, 1, hauteur, colors.orange)
    paintutils.drawLine(1, hauteur, largeur, hauteur, colors.orange)
    paintutils.drawLine(largeur, 1, largeur, largeur, colors.orange)
    --term.write(longueur, largeur)
    
    -- Remet la couleur de fond à blanc (ou autre couleur par défaut)
    s.setBackgroundColor(colors.black)
    s.setCursorPos(2, 2) -- repositionne pour éviter d'écrire sur le cadre
end

function drawTimer()
    if isExternalMonitor then
        term.setBackgroundColor(colors.orange)
        term.setTextColor(colors.white)
        term.setCursorPos(3, 7)
        term.write(formatTime(elapsed))
    end
end


function uiHandler()
    isPlaying = true
    videoscreen.setBackgroundColor(colors.black)
    videoscreen.clear()

    while true do
        if not programRunning then break end

        if isExternalMonitor then
            drawFrame(term)
            term.setCursorPos(3, 3)
            term.setBackgroundColor(colors.orange)
            if isPlaying then
                term.write("Pause")
            else
                term.write("Start")
            end
            term.setCursorPos(3, 5)
            term.write("Stop")

            local event, buttons, x, y = os.pullEvent("mouse_click")
            if x >= 3 and x <= 7 and y == 3 then
                if isPlaying then
                    isPlaying = false
                else
                    isPlaying = true
                end
            end
            if x >= 3 and x <= 6 and y == 5 then
                isPlaying = true
                programRunning = false
            end

            
        else
            local event, buttons, x, y = os.pullEvent("mouse_click")
            local width, height = term.getSize()
            
            if x >= 1 and x <= 4 and (height-1) == y then
                isPlaying = true
                programRunning = false
            end
            if x >= 1 and x <= 5 and y == (height-2) then
                if isPlaying then
                    isPlaying = false
                else
                    isPlaying = true
                end
            end
        end

    end

end

if command == "play" then
    fps, frames = load_metadata()
    videoscreen.clear()
    term.clear()
    if args[4] == "block" then
        blockUntilSignal()
    end
    startTimeSound = 0
    soundTime = 0
    videoTime = 0
    diff = 0

    isPlaying = true
    audioElapsed = 0
    startTimeSound = 0
    chunks = loadAudio()
    
    parallel.waitForAll(playAudio, playVideo, uiHandler)

elseif command == "download" then
    print(vid_adress)
    local monitor = peripheral.wrap("right")  

    -- Obtenir la taille en caractères
    local monwidth, monheight = videoscreen.getSize()

    local videoId = downloadVideo(adress .. "/download", vid_adress, monwidth, monheight)

    term.redirect(term.native())
    print("Video is uploading...")
    while not urlExists(adress .. "/videos/" .. videoId .. "/lock.txt") do
        os.sleep(2)
    end
    print("Video downloaded !")
    os.sleep(2)

    if args[4] == "block" then
        blockUntilSignal()
    end


    shell.run("vbc_bmi", "play", videoId)
    --print("Your video is now avaiable !")
    --print("--> vbc play", videoId)

end





