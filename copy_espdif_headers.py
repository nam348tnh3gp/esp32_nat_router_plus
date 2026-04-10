import os
import shutil
import sys
import subprocess
from pathlib import Path

# Lấy đường dẫn framework ESP-IDF từ PlatformIO
def get_espidf_include_path():
    try:
        # Tìm framework-espidf package
        result = subprocess.run(
            ['pio', 'run', '--target', 'clean', '--verbose'],
            capture_output=True, text=True, cwd=os.getcwd()
        )
    except:
        pass
    
    # Đường dẫn mặc định của PlatformIO packages
    home = Path.home()
    pio_packages = home / '.platformio' / 'packages'
    
    # Tìm framework-espidf
    framework_path = None
    for pkg in pio_packages.iterdir():
        if 'framework-espidf' in str(pkg):
            framework_path = pkg
            break
    
    if not framework_path:
        print("⚠️ Không tìm thấy framework-espidf, PlatformIO sẽ tự cài đặt...")
        return None
    
    include_path = framework_path / 'include' / 'espidf'
    if include_path.exists():
        return include_path
    
    # Thử đường dẫn khác
    alt_path = framework_path / 'tools' / 'include'
    if alt_path.exists():
        return alt_path
    
    return framework_path

# Danh sách headers cần copy từ ESP-IDF
REQUIRED_HEADERS = [
    'esp_system.h',
    'esp_log.h',
    'esp_wifi.h',
    'esp_event.h',
    'esp_netif.h',
    'esp_chip_info.h',
    'nvs_flash.h',
    'esp_task_wdt.h',
    'esp_http_server.h',
    'esp_temp_sensor.h',
    # LwIP headers
    'lwip/err.h',
    'lwip/sys.h',
    'lwip/netif.h',
    'lwip/priv/tcpip_priv.h',
    'lwip/etharp.h',
    'lwip/dns.h',
    'lwip/lwip_napt.h',
    # FreeRTOS
    'freertos/FreeRTOS.h',
    'freertos/task.h',
    'freertos/event_groups.h',
]

# Danh sách headers TỰ TẠO (từ code gốc ESP-IDF)
CUSTOM_HEADERS = [
    'cmd_decl.h',
    'router_globals.h',
    'get_data_handler.h',
    'auth_handler.h',
    'initialization.h',
    'hardware_handler.h',
    'web_server.h',
    'console_handler.h',
    'file_system.h',
    'mac_generator.h',
    'nvm.h',
    'router_handler.h',
    'wifi_init.h',
    'ota_handler.h',
]

def create_custom_header(header_name, dest_dir):
    """Tạo custom header với nội dung tối thiểu"""
    content_map = {
        'cmd_decl.h': '''
#ifndef CMD_DECL_H
#define CMD_DECL_H

#ifdef __cplusplus
extern "C" {
#endif

void register_system(void);
void register_nvs(void);
void register_router(void);
void start_console(void);
void initialize_console(void);

#ifdef __cplusplus
}
#endif

#endif
''',
        'router_globals.h': '''
#ifndef ROUTER_GLOBALS_H
#define ROUTER_GLOBALS_H

#include <stdint.h>
#include <stdbool.h>

extern uint16_t connect_count;
extern bool ap_connect;
extern uint32_t my_ip;
extern uint32_t my_ap_ip;
extern bool IsWebServerEnable;
extern void *server;

#endif
''',
        'initialization.h': '''
#ifndef INITIALIZATION_H
#define INITIALIZATION_H

void initialize_nvs(void);
void initialize_filesystem(void);
void parms_init(void);
void hardware_init(void);
void get_portmap_tab(void);
void ota_update_init(void);

#endif
''',
        'web_server.h': '''
#ifndef WEB_SERVER_H
#define WEB_SERVER_H

#include <stdbool.h>

extern bool IsWebServerEnable;
void *start_webserver(void);

#endif
''',
        'wifi_init.h': '''
#ifndef WIFI_INIT_H
#define WIFI_INIT_H

void wifi_init(void);

#endif
''',
        'hardware_handler.h': '''
#ifndef HARDWARE_HANDLER_H
#define HARDWARE_HANDLER_H

void hardware_init(void);

#endif
''',
        'nvm.h': '''
#ifndef NVM_H
#define NVM_H

// NVM functions

#endif
''',
        'console_handler.h': '''
#ifndef CONSOLE_HANDLER_H
#define CONSOLE_HANDLER_H

void initialize_console(void);
void start_console(void);
void register_system(void);
void register_nvs(void);
void register_router(void);

#endif
''',
        'file_system.h': '''
#ifndef FILE_SYSTEM_H
#define FILE_SYSTEM_H

void initialize_filesystem(void);

#endif
''',
        'ota_handler.h': '''
#ifndef OTA_HANDLER_H
#define OTA_HANDLER_H

void ota_update_init(void);

#endif
''',
        'get_data_handler.h': '''
#ifndef GET_DATA_HANDLER_H
#define GET_DATA_HANDLER_H

void get_portmap_tab(void);

#endif
''',
        'auth_handler.h': '''
#ifndef AUTH_HANDLER_H
#define AUTH_HANDLER_H

// Auth functions

#endif
''',
        'mac_generator.h': '''
#ifndef MAC_GENERATOR_H
#define MAC_GENERATOR_H

// MAC functions

#endif
''',
        'router_handler.h': '''
#ifndef ROUTER_HANDLER_H
#define ROUTER_HANDLER_H

void register_router(void);

#endif
''',
    }
    
    content = content_map.get(header_name, f'''
#ifndef {header_name.upper().replace('.', '_')}
#define {header_name.upper().replace('.', '_')}

// Auto-generated header for {header_name}

#endif
''')
    
    dest_path = dest_dir / header_name
    with open(dest_path, 'w') as f:
        f.write(content.strip())
    print(f"✅ Created: {dest_path}")

def copy_espidf_headers():
    print("=" * 60)
    print("📦 ESP-IDF Header Copier")
    print("=" * 60)
    
    # Tạo thư mục đích
    project_dir = Path(os.getcwd())
    include_dir = project_dir / 'include' / 'espidf'
    include_dir.mkdir(parents=True, exist_ok=True)
    
    # Tìm ESP-IDF framework
    espidf_path = get_espidf_include_path()
    
    if espidf_path and espidf_path.exists():
        print(f"📁 Found ESP-IDF at: {espidf_path}")
        
        # Copy từng header
        for header in REQUIRED_HEADERS:
            src = espidf_path / header
            if src.exists():
                dest = include_dir / header
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                print(f"✅ Copied: {header}")
            else:
                # Thử tìm trong thư mục con
                found = False
                for root, dirs, files in os.walk(espidf_path):
                    if header in files:
                        src = Path(root) / header
                        dest = include_dir / header
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dest)
                        print(f"✅ Copied: {header} (from {root})")
                        found = True
                        break
                if not found:
                    print(f"⚠️ Not found: {header}")
    else:
        print("⚠️ ESP-IDF not installed yet - PlatformIO will install it during build")
        print("   Headers will be available on next build")
    
    # Tạo custom headers (từ code gốc)
    custom_include_dir = project_dir / 'include' / 'custom'
    custom_include_dir.mkdir(parents=True, exist_ok=True)
    
    for header in CUSTOM_HEADERS:
        create_custom_header(header, custom_include_dir)
    
    # Tạo file main wrapper để include đúng đường dẫn
    main_wrapper = project_dir / 'src' / 'main_wrapper.cpp'
    wrapper_content = '''
// Wrapper để include đúng các headers
#include <Arduino.h>

// ESP-IDF headers
#include "espidf/esp_system.h"
#include "espidf/esp_log.h"
#include "espidf/esp_wifi.h"
#include "espidf/esp_event.h"
#include "espidf/esp_netif.h"
#include "espidf/nvs_flash.h"
#include "espidf/esp_task_wdt.h"
#include "espidf/lwip/lwip_napt.h"
#include "espidf/lwip/netif.h"
#include "espidf/lwip/priv/tcpip_priv.h"
#include "espidf/lwip/etharp.h"
#include "espidf/freertos/FreeRTOS.h"
#include "espidf/freertos/task.h"
#include "espidf/freertos/event_groups.h"

// Custom headers
#include "custom/cmd_decl.h"
#include "custom/router_globals.h"
#include "custom/get_data_handler.h"
#include "custom/auth_handler.h"
#include "custom/initialization.h"
#include "custom/hardware_handler.h"
#include "custom/web_server.h"
#include "custom/console_handler.h"
#include "custom/file_system.h"
#include "custom/mac_generator.h"
#include "custom/nvm.h"
#include "custom/router_handler.h"
#include "custom/wifi_init.h"
#include "custom/ota_handler.h"

// Include main code
#include "esp32_nat_router.cpp"
'''
    
    with open(main_wrapper, 'w') as f:
        f.write(wrapper_content.strip())
    print(f"✅ Created: {main_wrapper}")
    
    print("\n" + "=" * 60)
    print("✅ Header copy completed!")
    print("=" * 60)

# Chạy script
if __name__ == "__main__":
    copy_espidf_headers()
