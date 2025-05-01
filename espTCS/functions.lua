function mysplit (inputstr, sep)
        if sep == nil then
                sep = "%s"
        end
        local t={}
        for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
                table.insert(t, str)
        end
        return t
end

function quote_d (inputstr)
    return "\"" .. inputstr .. "\""
end

function trim2(s)
    return s:match "^%s*(.-)%s*$"
 end
 
function find_Body ( payload )
    if payload:find("Content%-Length:")==nil then return 0 end
    ContentLength = tonumber(string.match(payload, "%d+", payload:find("Content%-Length:")+16))
    return string.sub(payload,#payload-ContentLength,#payload)
end

function find_PostParameters ( post_ )
        local t={}
        for k,v in ipairs(post_) do
            if string.find(v,"mcu_do=")~=nil then 
                t.mcu_do=string.sub(v,string.find(v,"=")+1,#v)
                --table.insert(t, t.mcu_do)
                print(t.mcu_do)
            end
            if string.find(v,"switch=")~=nil then 
                t.switch=string.sub(v,string.find(v,"=")+1,#v)
                --table.insert(t, t.switch)
                print(t.switch)
            end
            if string.find(v,"reading=")~=nil then 
                t.reading=string.sub(v,string.find(v,"=")+1,#v)
                --table.insert(t, t.reading)
                print(t.reading)
            end         
        end     
        return t
end

--function string:split(pat)
--  pat = pat or '%s+'
--  local st, g = 1, self:gmatch("()("..pat..")")
--  local function getter(segs, seps, sep, cap1, ...)
--    st = sep and seps + #sep
--    return self:sub(segs, (seps or 0) - 1), cap1 or sep, ...
--  end
--  return function() if st then return getter(st, g()) end end
--end
