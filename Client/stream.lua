local fs = fs or require("cc.fs")
local http = http or require("cc.http")
local peripheral = peripheral or require("peripheral")
local bmi = require("bmi")

local args = {...}
local server_ip = args[1] or settings.get("vbc.stream_ip", true)

if not server_ip then
    error("Usage: stream <server_url>")
end

-- Automatically detect a connected monitor
local monitor_side
for _, side in ipairs(peripheral.getNames()) do
    if peripheral.getType(side) == "monitor" then
        monitor_side = side
        break
    end
end

if not monitor_side then
    mon = term
else

mon = peripheral.wrap(monitor_side)
mon.setTextScale(0.5)
end

local width, height = mon.getSize()

print("Detected monitor resolution:", width, height)
print("Server:", server_ip)

local local_path = "current_frame.bmi"

local opts = {
    char = string.char(127),
    term = mon
}

local function downloadFrame()
    local url = server_ip .. "/get_frame?width=" .. width .. "&height=" .. height
    local ok, resp = pcall(http.get, url)

    if not ok or not resp then
        return false
    end

    local data = resp.readAll()
    resp.close()

    if not data or #data == 0 then
        return false
    end

    local f = fs.open(local_path, "wb")
    f.write(data)
    f.close()

    return true
end

while true do
    if downloadFrame() then
        mon.setCursorPos(1,1)
        local ok = pcall(function()
            bmi.draw(local_path, opts)
        end)

        if not ok then
            mon.clear()
            mon.setCursorPos(1,1)
            mon.write("BMI Error")
        end
    else
        print("Frame not available")
    end
    if 

    sleep(0.1)
end