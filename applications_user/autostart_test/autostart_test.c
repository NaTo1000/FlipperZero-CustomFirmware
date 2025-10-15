#include <furi.h>
#include <gui/gui.h>
#include <input/input.h>

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    bool running;
} AutostartTestApp;

static void render_callback(Canvas* canvas, void* context) {
    (void)context;
    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 8, 26, "Autostart Test");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 8, 44, "Started on boot!");
    canvas_draw_str(canvas, 8, 60, "BACK to exit");
}

static void input_callback(InputEvent* event, void* context) {
    AutostartTestApp* app = context;
    if(event->type == InputTypeShort && event->key == InputKeyBack) {
        app->running = false;
    }
}

int32_t autostart_test_app(void* p) {
    (void)p;

    AutostartTestApp app = {0};

    app.gui = furi_record_open(RECORD_GUI);
    app.view_port = view_port_alloc();

    view_port_draw_callback_set(app.view_port, render_callback, &app);
    view_port_input_callback_set(app.view_port, input_callback, &app);

    gui_add_view_port(app.gui, app.view_port, GuiLayerFullscreen);

    app.running = true;
    while(app.running) {
        furi_delay_ms(20);
    }

    gui_remove_view_port(app.gui, app.view_port);
    view_port_free(app.view_port);
    furi_record_close(RECORD_GUI);

    return 0;
}