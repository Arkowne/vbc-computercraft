local args = { ... }

-- === Mode DEBUG ===
local debug = true

-- Initialise DFPWM
local dfpwm = require("cc.audio.dfpwm")
local decoder = dfpwm.make_decoder()

-- Vérification des arguments
local id = args[1]
if not id then
    print("\nVeuillez renseigner l'ID de votre vidéo.")
    print("Commande : vbc <id>")
    print("")
    os.pullEvent()
    return
end

-- Trouve le moniteur et le configure
local mon = peripheral.find("monitor")
if not mon then
    error("Aucun moniteur détecté.")
end

term.redirect(mon)
mon.setTextScale(0.5)
mon.clear()
local w, h = mon.getSize()

-- Variables de configuration
local adress = settings.get("vbc.ip_server", true)
fs.makeDir("temp")


-- Trouve le speaker et le configure
if args[2] ~= "no" then
    speaker = peripheral.find("speaker")
    if not speaker then
        error("Aucun speaker trouvÃ©")
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
    -- 1) Ouvrir la requÃªte HTTP
    local resp = http.get(url)
    if not resp then
        return false, "Ãchec du tÃ©lÃ©chargement", nil, nil
    end

    -- 2) Lire lâenâtÃªte Content-Length (nil si absent)
    local headers  = resp.getResponseHeaders()
    local declared = headers and tonumber(headers["Content-Length"])

    -- 3) Lire tout le contenu
    local data = resp.readAll()
    resp.close()

    -- 4) Sauvegarder sur le disque
    local f = fs.open(destPath, "wb")
    f.write(data)
    f.close()

    -- 5) Mesurer la taille rÃ©elle
    local actualSize = fs.getSize(destPath)

    -- 6) VÃ©rifier cohÃ©rence taille annoncÃ©e / rÃ©elle
    if declared and declared ~= actualSize then
        -- avertissement, mais on continue pour le checksum
        print(("â ï¸ Taille dÃ©clarÃ©e (%d) != taille rÃ©elle (%d)"):format(declared, actualSize))
    end

    -- 7) Calculer le checksum
    local actualSum = checksum(destPath)

    return true,
           "TÃ©lÃ©chargement et inspection terminÃ©s",
           actualSize,
           actualSum
end

function dl_audio(url)
    local path = "audio.dfpwm"
    print( "URL : " .. url)

    local ok, msg, size, sum = downloadAndInspect(url, path)
    if ok then
        print(("SuccÃ¨sâ¯: taille = %d octets, checksum = %u"):format(size, sum))
        return "succes"
    else
        print("Erreurâ¯: "..msg)
        return "error"
    end
end

local function loadAudio()
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

-- Joue tous les chunks dÃ©codÃ©s
local function playAudio()
    local chunks = loadAudio()
    for _, c in ipairs(chunks) do
        local pcm = decoder(c)
        while not speaker.playAudio(pcm) do
            os.pullEvent("speaker_audio_empty")  -- Attente que le speaker soit prÃªt pour jouer
        end
    end
end



local function displayBLT(path)
    local f = fs.open(path,"r")
    if not f then error("Cannot open "..path) end

    local y = 1
    while true do
        local txt = f.readLine()
        local fg  = f.readLine()
        local bg  = f.readLine()
        if not (txt and fg and bg) then break end

        local len = #txt
        if #fg < len then fg=fg..string.rep("0",len-#fg) end
        if #bg < len then bg=bg..string.rep("0",len-#bg) end

        term.setCursorPos(1, y)
        term.blit(txt, fg, bg)
        y = y + 1
    end
    f.close()
end

local function sendCommand(command, url)
    rednet.send(audio_computer_id, { command = command, url = url })
    local _, response = rednet.receive(2)
    if response then
        print("Réponse : " .. response.status .. " - " .. response.message)
    else
        print("Aucune réponse reçue.")
    end
end

local function dl_image(url, fileName)
    local resp = http.get(url)
    if not resp then
        print("Échec téléchargement : " .. url)
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
    end
    local content = file.readAll()
    file.close()

    local fps = tonumber(content:match("fps=(%d+)"))
    local frames = tonumber(content:match("frames=(%d+)"))
    print("FPS :", fps)
    print("Nombre de frames :", frames)
    return fps, frames
end

if args[2] ~= "no" then
    state = dl_audio(adress .. "/videos/" .. id .. "/audio.dfpwm")
    if state == "error" then
        error("Impossible de prÃ©charger l'audio.")
    else
        print("Audio telecharge.")
    end
end

local fps, frames = load_metadata()


function file_exists(path)
    local file = io.open(path, "r")
    if file then
        file:close()
        return true
    else
        return false
    end
end

mon.clear()

function playVideo()
    sleep(1)


    -- Demarage de la video
    while i < frames do
        local now = os.clock()

        -- Recalage toutes les 5 secondes
        if now - lastSync >= 5 then
            local elapsed = math.ceil(now - startTime)
            i = elapsed * fps
            lastSync = now
            if i >= frames then break end
        end

        local index = string.format("%05d", i)
        local url = adress .. "/videos/" .. id .. "/frame_" .. index .. ".blt"
        local path = "temp/frame_" .. index .. ".blt"

        if dl_image(url, path) and file_exists(path) then
            displayBLT(path)
            fs.delete(path)
        else
            print("Impossible de télécharger ou d'afficher l'image : " .. path)
        end

        if args[3] == "debug" then
            local debugText = string.format("Frame: %d/%d | Time: %.2fs", i, frames, now - startTime)
            term.setCursorPos(1, h)
            term.setTextColor(colors.white)
            term.clearLine()
            write(debugText)
        end

        i = i + 1
        sleep(1 / fps)
    end
end

    -- === Lecture synchronisée avec correction toutes les 5 secondes ===
startTime = os.clock()
astSync = startTime
i = 0

parallel.waitForAll(playAudio, playVideo)


mon.clear()
