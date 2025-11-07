--[[
    Installation script for ComputerCraft
    Downloads two files from the Internet
]]

-- Define URLs and local save paths
local files_to_download = {
    {url = "https://github.com/Arkowne/vbc-computercraft/raw/refs/heads/main/Client/vbc.lua", path = "vbc.lua"},
    {url = "https://github.com/Arkowne/vbc-computercraft/raw/refs/heads/main/Client/bmi.lua", path = "bmi.lua"}
}

-- Function to download a file
local function download_file(url, path)
    if not http then
        error("HTTP is not enabled on this computer.")
    end

    print("Downloading " .. url .. " ...")
    local response = http.get(url)
    if not response then
        print("Error downloading " .. url)
        return false
    end

    local content = response.readAll()
    response.close()

    local file = fs.open(path, "w")
    file.write(content)
    file.close()

    print("File saved as: " .. path)
    return true
end

-- Download all files
for _, file_info in ipairs(files_to_download) do
    download_file(file_info.url, file_info.path)
end

print("✅ All files have been downloaded!")
