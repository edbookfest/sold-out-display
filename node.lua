util.init_hosted()

gl.setup(NATIVE_WIDTH, NATIVE_HEIGHT)

node.alias("sold-out")

local font
local logo_asset_name
local logo
local black = resource.create_colored_texture(0,0,0,0.8)

node.event("content_update", function(filename, file)
    if filename == "config.json" then
        if CONFIG.auto_resolution then
            gl.setup(NATIVE_WIDTH, NATIVE_HEIGHT)
        else
            gl.setup(CONFIG.width, CONFIG.height)
        end
        font = CONFIG.font
        if CONFIG.logo.asset_name ~= logo_asset_name then
            logo_asset_name = CONFIG.logo.asset_name
            logo = resource.load_image(logo_asset_name, TRUE)
        end
    end
end)

local start = 0
local count = 0
local current_page = 1

local total_pages = 1
local next_page = sys.now() + CONFIG.switch_time
local soldoutevents = {}
local magic_dot = " "

util.file_watch("soldoutevents.txt", function(content)
    soldoutevents = {}
    if content ~= "" then
        for event in string.gmatch(content, "[^\r\n]+") do
            soldoutevents[#soldoutevents + 1] = event
        end
        print("There are " .. #soldoutevents .. " sold out events")
    end
    if #soldoutevents == 0 then
        soldoutevents[#soldoutevents + 1] = CONFIG.no_events_text
        print("There are no sold out events")
    end
    total_pages = math.ceil(#soldoutevents / CONFIG.events_per_page)
end)
util.file_watch("last_updated.txt", function(content)
    magic_dot = " "
    if content == "updating now" then
        magic_dot = "."
    end
end)

local function load_next()
    next_page = sys.now() + CONFIG.switch_time
    start = start + count
    current_page = current_page + 1
end

local function start_again()
    start = 0
    count = 0
    current_page = 1
end

local function stringLongerThanScreen(str)
    local width = font:width(str, CONFIG.font_size)
    if width > WIDTH - (CONFIG.margin * 2) then
        return true
    end
    return false
end

local function shortenString(str, no_chars)
    no_chars = no_chars or 1
    local length = string.len(str)
    return string.sub(str, 0, length - no_chars)
end

local function write_event(event)
    local str = event
    while (stringLongerThanScreen(str))
    do
        str = shortenString(str)
        event = shortenString(str, 3)
        event = event .. '...'
    end
    font:write(CONFIG.margin, y, event, CONFIG.font_size, CONFIG.font_colour.rgba())
    y = y + CONFIG.font_size
    return 1
end

function node.render()
    CONFIG.background_colour.clear()

    -- print title
    local title = "Sold out events"
    if CONFIG.today_only then
        title = title .. " today"
    end
    local title_font_size = CONFIG.font_size * 1.5
    local title_width = font:width(title, title_font_size)
    font:write(CONFIG.margin, CONFIG.margin, title, title_font_size, CONFIG.font_colour.rgba())
    black:draw(CONFIG.margin, CONFIG.margin + title_font_size, CONFIG.margin + title_width, CONFIG.margin + title_font_size + 1)

    -- draw logo
    local logo_w, logo_h = logo:size()
    local logo_ratio = logo_w / logo_h
    util.draw_correct(logo, WIDTH - (CONFIG.margin + (logo_ratio * title_font_size)), CONFIG.margin, WIDTH - CONFIG.margin, CONFIG.margin + title_font_size)

    y = title_font_size + (title_font_size / 2 ) + CONFIG.margin
    count = 0
    local line_count = 0
    local pages = 0
    local morelines = 0
    for i, event in ipairs(soldoutevents) do
        if i > start then
            if line_count < CONFIG.events_per_page then
                local lines_consumed = write_event(event)
                y = y + (CONFIG.font_size / 2)
                count = count + 1
                line_count = line_count + lines_consumed
            else
                morelines = 1
            end
        end
    end

    if morelines == 1 then
        if current_page >= total_pages then
            total_pages = current_page + 1
        end
    end

    -- print number of pages
    local text = "Page  " .. current_page .. "/" .. total_pages .. magic_dot
    local size = CONFIG.font_size * 0.8
    local width = font:width(text, size)
    font:write(WIDTH - width - CONFIG.margin, HEIGHT - size - CONFIG.margin, text, size, CONFIG.font_colour.rgba())

    -- handle loading next pages
    if current_page < total_pages then
        if sys.now() > next_page then
            load_next()
        end
    else
        if sys.now() > next_page then
            load_next()
            start_again()
        end
    end
end
