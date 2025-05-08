local speaker = peripheral.find("speaker")
if not speaker then
    error("Aucun speaker trouvé")
end

-- Initialise DFPWM
local dfpwm = require("cc.audio.dfpwm")
local decoder = dfpwm.make_decoder()

-- Charge audio en chunks
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
    -- 1) Ouvrir la requête HTTP
    local resp = http.get(url)
    if not resp then
        return false, "Échec du téléchargement", nil, nil
    end

    -- 2) Lire l’en‑tête Content-Length (nil si absent)
    local headers  = resp.getResponseHeaders()
    local declared = headers and tonumber(headers["Content-Length"])

    -- 3) Lire tout le contenu
    local data = resp.readAll()
    resp.close()

    -- 4) Sauvegarder sur le disque
    local f = fs.open(destPath, "wb")
    f.write(data)
    f.close()

    -- 5) Mesurer la taille réelle
    local actualSize = fs.getSize(destPath)

    -- 6) Vérifier cohérence taille annoncée / réelle
    if declared and declared ~= actualSize then
        -- avertissement, mais on continue pour le checksum
        print(("⚠️ Taille déclarée (%d) != taille réelle (%d)"):format(declared, actualSize))
    end

    -- 7) Calculer le checksum
    local actualSum = checksum(destPath)

    return true,
           "Téléchargement et inspection terminés",
           actualSize,
           actualSum
end


function dl_audio(url)
    local path = "audio.dfpwm"
    print( "URL : " .. url)

    local ok, msg, size, sum = downloadAndInspect(url, path)
    if ok then
        print(("Succès : taille = %d octets, checksum = %u"):format(size, sum))
        return "succes"
    else
        print("Erreur : "..msg)
        return "error"
    end
end



-- Joue tous les chunks décodés
local function playAudio()
    local chunks = loadAudio()
    for _, c in ipairs(chunks) do
        local pcm = decoder(c)
        while not speaker.playAudio(pcm) do
            os.pullEvent("speaker_audio_empty")  -- Attente que le speaker soit prêt pour jouer
        end
    end
end

-- Ouverture du réseau
rednet.open(settings.get("vbc_hifi.side", true))  -- Adapter selon la position de votre modem

-- Thread de gestion des commandes audio
parallel.waitForAny(
    function()
        while true do
            local id, msg = rednet.receive()
            local command = msg.command

            if command == "preload" then
                -- Préchargement du fichier audio
                state = dl_audio(msg.url)
                if state == "error" then
                    error("Impossible de précharger l'audio.")
                end
                local file = fs.open("audio.dfpwm", "r")
                if not file then
                    error("Impossible de précharger l'audio.")
                end

            elseif command == "play" then
                -- Lecture de l'audio
                print("Lecture de l'audio démarrée.")
                
                rednet.send(id, { status = "ok", message = "Lecture démarrée" })

                playAudio()

            elseif command == "stop" then
                -- Arrêter la lecture
                speaker.stop()
                rednet.send(id, { status = "ok", message = "Lecture arrêtée" })
            else
                rednet.send(id, { status = "error", message = "Commande inconnue" })
            end
        end
    end
)
