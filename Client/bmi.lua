local bmi = {}

local CC_HEX = "0123456789abcdef"

local function BitReader(data)
    local pos, bitbuf, bits = 1, 0, 0
    local bytes = {data:byte(1, -1)}
    local len = #bytes

    local function read_bits(n)
        while bits < n and pos <= len do
            bitbuf = bitbuf * 256 + bytes[pos]
            bits = bits + 8
            pos = pos + 1
        end
        if bits < n then return 0 end
        bits = bits - n
        local val = bit32.rshift(bitbuf, bits)
        bitbuf = bit32.band(bitbuf, bit32.lshift(1, bits) - 1)
        return val
    end

    return { read_bits = read_bits }
end

-- Tableau direct pour les 16 couleurs hex
local HEX_TO_CC_ARRAY = {
    colors.white, colors.orange, colors.magenta, colors.lightBlue,
    colors.yellow, colors.lime, colors.pink, colors.gray,
    colors.lightGray, colors.cyan, colors.purple, colors.blue,
    colors.brown, colors.green, colors.red, colors.black
}

function bmi.draw(filename, opts)
    opts = opts or {}
    local PIX = opts.char or string.char(127)
    local scr = opts.term or term

    -- Lecture du fichier .bmi
    local f = fs.open(filename, "rb")
    if not f then error("fichier introuvable") end
    local raw = f.readAll()
    f.close()

    local w = raw:byte(1) * 256 + raw:byte(2)
    local h = raw:byte(3) * 256 + raw:byte(4)
    local data = raw:sub(5)
    local r = BitReader(data)

    for y = 1, h do
        local segments = {}
        local segment = {}
        local last_bg, last_fg
        local cursor_x = 1

        for x = 1, w do
            local skip = r.read_bits(1)
            if skip == 0 then
                local bg = HEX_TO_CC_ARRAY[r.read_bits(4) + 1]
                local fg = HEX_TO_CC_ARRAY[r.read_bits(4) + 1]

                -- Nouveau segment si couleur différente
                if bg ~= last_bg or fg ~= last_fg then
                    if #segment > 0 then
                        table.insert(segments, {bg=last_bg, fg=last_fg, text=table.concat(segment), x=cursor_x})
                        cursor_x = cursor_x + #segment
                        segment = {}
                    end
                    last_bg, last_fg = bg, fg
                end

                segment[#segment+1] = PIX
            else
                -- Pixel skip : terminer le segment actuel
                if #segment > 0 then
                    table.insert(segments, {bg=last_bg, fg=last_fg, text=table.concat(segment), x=cursor_x})
                    cursor_x = cursor_x + #segment
                    segment = {}
                    last_bg, last_fg = nil, nil
                end
                -- Avancer le curseur d’une position pour le skip
                cursor_x = cursor_x + 1
            end
        end

        -- Ajouter le dernier segment si nécessaire
        if #segment > 0 then
            table.insert(segments, {bg=last_bg, fg=last_fg, text=table.concat(segment), x=cursor_x})
        end

        -- Écriture de tous les segments
        for _, seg in ipairs(segments) do
            scr.setCursorPos(seg.x, y)
            scr.setBackgroundColor(seg.bg)
            scr.setTextColor(seg.fg)
            scr.write(seg.text)
        end
    end
end



return bmi
