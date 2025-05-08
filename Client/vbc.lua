local args = { ... }

-- === Mode DEBUG ===
local debug = true

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

if args[2] ~= "no" then
    local side_audio = settings.get("vbc.side_audio", true)
    audio_computer_id = settings.get("vbc.audio_id", true)
    rednet.open(side_audio)
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
    print("Téléchargement de l'audio...")
    sendCommand("preload", adress .. "/videos/" .. id .. "/audio.dfpwm")
    sleep(3)
    print("Audio téléchargé.")
end

local fps, frames = load_metadata()
if args[2] ~= "no" then
    sendCommand("play")
    sleep(0.5)
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

mon.clear()

-- === Lecture synchronisée avec correction toutes les 5 secondes ===
local startTime = os.clock()
local lastSync = startTime
local i = 0

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

mon.clear()
