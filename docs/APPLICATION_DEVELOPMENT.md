# Application Development Guide

Complete guide to developing custom applications for Flipper Zero with this custom firmware.

## Table of Contents

- [Quick Start](#quick-start)
- [Application Structure](#application-structure)
- [Manifest File (application.fam)](#manifest-file-applicationfam)
- [Basic Application Template](#basic-application-template)
- [SDK Overview](#sdk-overview)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)
- [Testing](#testing)
- [Debugging](#debugging)

## Quick Start

### Create Your First App

1. **Create application directory**:
   ```bash
   cd FlipperZero-CustomFirmware/applications_user
   mkdir hello_world
   cd hello_world
   ```

2. **Create manifest** (`application.fam`):
   ```python
   App(
       appid="hello_world",
       name="Hello World",
       apptype=FlipperAppType.EXTERNAL,
       entry_point="hello_world_app",
       sources=["hello_world.c"],
       fap_category="Misc",
       stack_size=1024,
   )
   ```

3. **Create source file** (`hello_world.c`):
   ```c
   #include <furi.h>
   #include <gui/gui.h>
   #include <input/input.h>

   typedef struct {
       Gui* gui;
       ViewPort* view_port;
       FuriMessageQueue* event_queue;
   } HelloWorldApp;

   static void render_callback(Canvas* canvas, void* ctx) {
       canvas_clear(canvas);
       canvas_set_font(canvas, FontPrimary);
       canvas_draw_str(canvas, 30, 30, "Hello, World!");
   }

   static void input_callback(InputEvent* input_event, void* ctx) {
       HelloWorldApp* app = ctx;
       furi_message_queue_put(app->event_queue, input_event, FuriWaitForever);
   }

   int32_t hello_world_app(void* p) {
       UNUSED(p);
       
       HelloWorldApp* app = malloc(sizeof(HelloWorldApp));
       app->event_queue = furi_message_queue_alloc(8, sizeof(InputEvent));
       
       app->gui = furi_record_open(RECORD_GUI);
       app->view_port = view_port_alloc();
       
       view_port_draw_callback_set(app->view_port, render_callback, app);
       view_port_input_callback_set(app->view_port, input_callback, app);
       
       gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);
       
       InputEvent event;
       bool running = true;
       
       while(running) {
           if(furi_message_queue_get(app->event_queue, &event, 100) == FuriStatusOk) {
               if(event.type == InputTypeShort && event.key == InputKeyBack) {
                   running = false;
               }
           }
       }
       
       gui_remove_view_port(app->gui, app->view_port);
       view_port_free(app->view_port);
       furi_record_close(RECORD_GUI);
       furi_message_queue_free(app->event_queue);
       free(app);
       
       return 0;
   }
   ```

4. **Build and test**:
   ```bash
   # Copy to unleashed-firmware
   cp -r applications_user/hello_world ../unleashed-firmware/applications_user/
   
   # Build
   cd ../unleashed-firmware
   ./fbt
   
   # Flash to device
   ./fbt flash_usb
   ```

## Application Structure

### File Organization

```
applications_user/
└── your_app/
    ├── application.fam          # Manifest (required)
    ├── your_app.c              # Main source (required)
    ├── your_app_i.h            # Internal header (optional)
    ├── scenes/                 # Scene modules (optional)
    │   ├── your_app_scene_main.c
    │   └── your_app_scene_config.c
    ├── views/                  # Custom views (optional)
    │   └── your_app_view.c
    ├── icons/                  # Icons and assets (optional)
    │   ├── icon_10x10.png
    │   └── animation_14x14/
    └── README.md              # Documentation (recommended)
```

### Naming Conventions

- **Identifiers**: `snake_case`
- **Types/Structs**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case`

Example:
```c
#define MAX_BUFFER_SIZE 256

typedef struct {
    uint8_t value;
} MyAppData;

static void my_app_render_callback(Canvas* canvas, void* context) {
    // Implementation
}
```

## Manifest File (application.fam)

### Basic Manifest

```python
App(
    appid="my_app",                    # Unique identifier
    name="My Application",             # Display name in menu
    apptype=FlipperAppType.EXTERNAL,   # Application type
    entry_point="my_app_main",         # Entry function name
    sources=["my_app.c"],              # Source files
    fap_category="Misc",               # Menu category
    stack_size=1024,                   # Stack size in bytes
)
```

### Advanced Manifest

```python
App(
    appid="advanced_app",
    name="Advanced App",
    apptype=FlipperAppType.EXTERNAL,
    entry_point="advanced_app_main",
    
    # Source files
    sources=[
        "advanced_app.c",
        "scenes/*.c",
        "views/*.c",
    ],
    
    # Resources
    fap_icon="icon.png",               # 10x10 px icon
    fap_category="Tools",              # Category in menu
    
    # Additional resources
    fap_icon_assets="icons",           # Icon directory
    fap_icon_assets_symbol="advanced_app",
    
    # Dependencies
    requires=[
        "gui",
        "storage",
    ],
    
    # Memory
    stack_size=2048,                   # Increase if needed
    order=10,                          # Menu order
)
```

### Available Categories

- `Tools`: Utility applications
- `GPIO`: Hardware interfacing
- `Sub-GHz`: Radio applications
- `RFID`: RFID/NFC tools
- `Infrared`: IR applications
- `Bluetooth`: BLE applications
- `Games`: Entertainment
- `Misc`: Everything else

## Basic Application Template

### Minimal Application

```c
#include <furi.h>
#include <gui/gui.h>

int32_t my_app_main(void* p) {
    UNUSED(p);
    
    // Your application logic here
    
    return 0;
}
```

### GUI Application Template

```c
#include <furi.h>
#include <gui/gui.h>
#include <input/input.h>

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    FuriMessageQueue* event_queue;
    // Add your app state here
} MyApp;

static void my_app_render(Canvas* canvas, void* ctx) {
    MyApp* app = ctx;
    
    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 10, 20, "My Application");
    
    // Draw your UI here
}

static void my_app_input(InputEvent* input_event, void* ctx) {
    MyApp* app = ctx;
    furi_message_queue_put(app->event_queue, input_event, FuriWaitForever);
}

int32_t my_app_main(void* p) {
    UNUSED(p);
    
    // Allocate app structure
    MyApp* app = malloc(sizeof(MyApp));
    app->event_queue = furi_message_queue_alloc(8, sizeof(InputEvent));
    
    // Open GUI record
    app->gui = furi_record_open(RECORD_GUI);
    
    // Allocate viewport
    app->view_port = view_port_alloc();
    view_port_draw_callback_set(app->view_port, my_app_render, app);
    view_port_input_callback_set(app->view_port, my_app_input, app);
    
    // Add viewport to GUI
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);
    
    // Main event loop
    InputEvent event;
    bool running = true;
    
    while(running) {
        if(furi_message_queue_get(app->event_queue, &event, 100) == FuriStatusOk) {
            if(event.type == InputTypeShort && event.key == InputKeyBack) {
                running = false;
            }
            
            // Handle other input events
            if(event.type == InputTypeShort) {
                switch(event.key) {
                    case InputKeyUp:
                        // Handle up
                        break;
                    case InputKeyDown:
                        // Handle down
                        break;
                    case InputKeyLeft:
                        // Handle left
                        break;
                    case InputKeyRight:
                        // Handle right
                        break;
                    case InputKeyOk:
                        // Handle OK
                        break;
                    default:
                        break;
                }
            }
            
            // Request redraw
            view_port_update(app->view_port);
        }
    }
    
    // Cleanup
    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    furi_record_close(RECORD_GUI);
    furi_message_queue_free(app->event_queue);
    free(app);
    
    return 0;
}
```

## SDK Overview

### Core Includes

```c
#include <furi.h>              // Core RTOS and utilities
#include <gui/gui.h>           // GUI system
#include <input/input.h>       // Input handling
#include <storage/storage.h>   // File system
#include <notification/notification.h>  // LEDs, vibration
#include <dialogs/dialogs.h>   // System dialogs
```

### Common Data Types

```c
// Boolean
bool flag = true;

// Integers
uint8_t byte = 255;
uint16_t word = 65535;
uint32_t dword = 4294967295;
int32_t signed_value = -100;

// Strings
FuriString* str = furi_string_alloc();
furi_string_set(str, "Hello");
furi_string_free(str);

// Timing
uint32_t ticks = furi_get_tick();
furi_delay_ms(100);
```

### Memory Management

```c
// Allocation
void* ptr = malloc(size);
if(ptr == NULL) {
    // Handle allocation failure
}

// Always free
free(ptr);

// String allocation
FuriString* str = furi_string_alloc();
// ... use string ...
furi_string_free(str);
```

### Canvas Drawing

```c
// Clear canvas
canvas_clear(canvas);

// Set font
canvas_set_font(canvas, FontPrimary);    // Large
canvas_set_font(canvas, FontSecondary);  // Small

// Draw text
canvas_draw_str(canvas, x, y, "Text");
canvas_draw_str_aligned(canvas, x, y, AlignCenter, AlignCenter, "Text");

// Draw shapes
canvas_draw_line(canvas, x1, y1, x2, y2);
canvas_draw_box(canvas, x, y, width, height);
canvas_draw_frame(canvas, x, y, width, height);
canvas_draw_circle(canvas, x, y, radius);

// Draw icons
canvas_draw_icon(canvas, x, y, &I_icon_name);
```

### Input Handling

```c
typedef enum {
    InputKeyUp,
    InputKeyDown,
    InputKeyRight,
    InputKeyLeft,
    InputKeyOk,
    InputKeyBack,
} InputKey;

typedef enum {
    InputTypePress,      // Key pressed
    InputTypeRelease,    // Key released
    InputTypeShort,      // Short press
    InputTypeLong,       // Long press
    InputTypeRepeat,     // Repeat event
} InputType;
```

## Common Patterns

### File Operations

```c
#include <storage/storage.h>

// Open storage
Storage* storage = furi_record_open(RECORD_STORAGE);

// Open file
File* file = storage_file_alloc(storage);
if(storage_file_open(file, "/ext/myapp/data.txt", FSAM_READ, FSOM_OPEN_EXISTING)) {
    // Read data
    uint8_t buffer[256];
    size_t bytes_read = storage_file_read(file, buffer, sizeof(buffer));
    
    storage_file_close(file);
}

storage_file_free(file);
furi_record_close(RECORD_STORAGE);
```

### Notifications (LED, Vibration)

```c
#include <notification/notification.h>

NotificationApp* notifications = furi_record_open(RECORD_NOTIFICATION);

// Send notification
notification_message(notifications, &sequence_blink_blue_10);
notification_message(notifications, &sequence_success);
notification_message(notifications, &sequence_error);

furi_record_close(RECORD_NOTIFICATION);
```

### Dialogs

```c
#include <dialogs/dialogs.h>

DialogsApp* dialogs = furi_record_open(RECORD_DIALOGS);

// Message dialog
DialogMessage* message = dialog_message_alloc();
dialog_message_set_header(message, "Title", 64, 3, AlignCenter, AlignTop);
dialog_message_set_text(message, "Message text", 64, 32, AlignCenter, AlignCenter);
dialog_message_set_buttons(message, "Cancel", "OK", NULL);

DialogMessageButton result = dialog_message_show(dialogs, message);
if(result == DialogMessageButtonRight) {
    // OK pressed
}

dialog_message_free(message);
furi_record_close(RECORD_DIALOGS);
```

## Best Practices

### Resource Management

1. **Always free allocated resources**:
   ```c
   void* ptr = malloc(size);
   // ... use ptr ...
   free(ptr);  // Don't forget!
   ```

2. **Close records**:
   ```c
   Gui* gui = furi_record_open(RECORD_GUI);
   // ... use gui ...
   furi_record_close(RECORD_GUI);
   ```

3. **Handle allocation failures**:
   ```c
   void* ptr = malloc(size);
   if(ptr == NULL) {
       // Handle error, cleanup, and return
       return -1;
   }
   ```

### Error Handling

```c
bool my_app_load_data(MyApp* app) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    File* file = storage_file_alloc(storage);
    
    bool success = false;
    
    if(storage_file_open(file, "/ext/data.bin", FSAM_READ, FSOM_OPEN_EXISTING)) {
        uint8_t buffer[256];
        if(storage_file_read(file, buffer, sizeof(buffer)) > 0) {
            // Process data
            success = true;
        }
        storage_file_close(file);
    }
    
    storage_file_free(file);
    furi_record_close(RECORD_STORAGE);
    
    return success;
}
```

### Performance

1. **Avoid blocking operations**:
   ```c
   // Bad: blocks event loop
   furi_delay_ms(5000);
   
   // Good: use timer or check elapsed time
   uint32_t start_time = furi_get_tick();
   while(furi_get_tick() - start_time < 5000) {
       // Process events
       if(furi_message_queue_get(queue, &event, 100) == FuriStatusOk) {
           // Handle event
       }
   }
   ```

2. **Optimize rendering**:
   ```c
   static void render_callback(Canvas* canvas, void* ctx) {
       // Only draw what's necessary
       // Cache expensive calculations
       // Use appropriate fonts
   }
   ```

### Stack Usage

Monitor and adjust stack size if needed:

```c
// In application.fam
stack_size=2048,  // Increase if app crashes

// In code, use stack conservatively
void my_function() {
    // Avoid large local arrays
    uint8_t small_buffer[64];  // OK
    // uint8_t large_buffer[1024];  // May overflow stack!
    
    // Use malloc for large buffers
    uint8_t* large_buffer = malloc(1024);
    // ... use buffer ...
    free(large_buffer);
}
```

## Testing

### On-Device Testing

1. **Build and flash**:
   ```bash
   ./fbt flash_usb
   ```

2. **Test all features**:
   - Input handling
   - UI rendering
   - File operations
   - Error conditions

3. **Monitor serial output**:
   ```bash
   screen /dev/ttyACM0 115200
   ```

### Debug Logging

```c
#include <furi.h>

// Log levels
FURI_LOG_E("MyApp", "Error message");      // Error
FURI_LOG_W("MyApp", "Warning message");    // Warning
FURI_LOG_I("MyApp", "Info message");       // Info
FURI_LOG_D("MyApp", "Debug message");      // Debug
FURI_LOG_T("MyApp", "Trace message");      // Trace

// With formatting
FURI_LOG_I("MyApp", "Value: %d", value);
FURI_LOG_E("MyApp", "Error %d: %s", code, message);
```

## Debugging

### Common Issues

1. **App crashes immediately**:
   - Check stack size
   - Verify pointer initialization
   - Look for NULL dereferences

2. **UI doesn't update**:
   - Call `view_port_update()`
   - Check render callback is set
   - Verify viewport is added to GUI

3. **Input not working**:
   - Set input callback
   - Check event queue
   - Verify proper input handling

4. **Memory leaks**:
   - Free all allocated memory
   - Close all opened records
   - Free all created objects

### Debug Tools

```c
// Assert conditions
furi_assert(ptr != NULL);
furi_assert(value < MAX_VALUE);

// Check conditions
furi_check(storage_file_open(...));

// Halt on error
furi_crash("Critical error occurred");
```

## Examples

See the `applications_user/autostart_test/` directory for a complete working example.

## Next Steps

- Study existing Flipper applications
- Experiment with different UI layouts
- Add file storage to your app
- Implement scene-based navigation
- Create custom views
- Add settings and configuration

## Resources

- [Flipper Zero SDK Documentation](https://docs.flipperzero.one/)
- [Unleashed Firmware Repository](https://github.com/DarkFlippers/unleashed-firmware)
- [Flipper Development Discord](https://flipperzero.one/discord)

---

Happy coding! 🚀
