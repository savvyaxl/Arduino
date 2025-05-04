WIFI_SSID = "829D_Fibra"
WIFI_PASSWORD = "TheElephantLeftTheBrownCowDeadAt10AM"

wifi_got_ip_event = function(T)
  local site = "wikipedia.org"
  -- Note: Having an IP address does not mean there is internet access!
  -- Internet connectivity can be determined with net.dns.resolve().
  print("WiFi connection is established! IP address is: " .. T.IP)
  print("DNS server 1: " .. net.dns.getdnsserver(0))
  print("DNS server 2: " .. net.dns.getdnsserver(1))
  net.dns.resolve(site, function(sk, ip)
    if (ip == nil) then
      print("DNS fail!")
    else
      print("Connected to the internet")
      print(site .. " IP: " .. ip)
    end
  end)
end

wifi.eventmon.register(wifi.eventmon.STA_GOT_IP, wifi_got_ip_event)

print("Connecting to WiFi access point...")
wifi.setmode(wifi.STATION)
wifi.sta.config({ ssid = WIFI_SSID, pwd = WIFI_PASSWORD })