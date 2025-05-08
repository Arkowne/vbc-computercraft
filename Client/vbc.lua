local args = { ... }

-- === Mode DEBUG ===
local debug = true

-- Initialise DFPWM
local dfpwm = require("cc.audio.dfpwm")
local decoder = dfpwm.make_decoder()

-- VÃ©rification des arguments
local id = args[1]
if not id then
    print("\nVeuillez renseigner l'ID de votre vidÃ©o.")
    print("Commande : vbc <id>")
    print("")
    os.pullEvent()
    return
end

-- Trouve le moniteur et le configure
local mon = peripheral.find("monitor")
if not mon then
    error("Aucun moniteur dÃ©tectÃ©.")
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
        error("Aucun speaker trouvÃÂ©")
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

-- Joue tous les chunks dÃÂ©codÃÂ©s
local function playAudio()
    startTimeSound = os.clock()
    for _, c in ipairs(chunks) do
        local pcm = decoder(c)
        while not speaker.playAudio(pcm) do
            os.pullEvent("speaker_audio_empty")  -- Attente que le speaker soit prÃÂªt pour joue
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
        term.blit(string.rep( string.char( 127 ), len ), fg, bg)
        y = y + 1
    end
    f.close()
end


local function dl_image(url, fileName)
    local resp = http.get(url)
    if not resp then
        print("Ãchec tÃ©lÃ©chargement : " .. url)
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
        error("Impossible de prÃÂ©charger l'audio.")
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
    -- === Lecture synchronisÃ©e avec correction toutes les 5 secondes ===
    startTime = os.clock()
    local lastSync = startTime
    local i = 0

    -- Demarage de la video
    while i < frames do
        local now = os.clock()
        i = math.ceil((now - startTimeSound)*fps)
        local index = string.format("%05d", i)
        local url = adress .. "/videos/" .. id .. "/frame_" .. index .. ".blt"
        local path = "temp/frame_" .. index .. ".blt"

        if dl_image(url, path) and file_exists(path) then
            displayBLT(path)
            fs.delete(path)
        else
            print("Impossible de tÃ©lÃ©charger ou d'afficher l'image : " .. path)
        end

        if args[3] == "debug" then
            local debugText = string.format("Frame: %d/%d | Time: %.2fs", i, frames, now - startTimeSound)
            term.setCursorPos(1, h)
            term.setTextColor(colors.white)
            term.clearLine()
            now = os.clock()
            soundTime = os.clock() - startTimeSound
            diff = videoTime - soundTime
            write(debugText .. " | FPS: " .. fps)
        end

        i = i + 1
        sleep(1 / fps)
    end
end

startTimeSound = 0
soundTime = 0
videoTime = 0
diff = 0
chunks = loadAudio()
parallel.waitForAll(playAudio, playVideo)



