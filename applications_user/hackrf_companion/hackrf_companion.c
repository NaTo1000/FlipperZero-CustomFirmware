/**
 * hackrf_companion.c
 *
 * HackRF Companion – Flipper Zero SDR Control Panel
 * =================================================
 * A four-view SDR-inspired application for the Flipper Zero that uses
 * the on-board CC1101 Sub-GHz radio to deliver live RF metrics,
 * a frequency scanner, an RSSI history monitor, and a settings panel.
 *
 * Inspired by the HackRF One tool suite (hackrf-2026.01.3)
 * Reference: NetBSD pkgsrc/ham/hackrf commit 942409583457d1c245fc28d959b845b9bcff5888
 *
 * Views (navigate with ← / →):
 *   [1] Dashboard  – current freq, live RSSI bar, modulation
 *   [2] Scanner    – spectrum sweep across the selected band
 *   [3] Monitor    – scrolling RSSI history graph
 *   [4] Settings   – frequency preset, modulation, scan-band selection
 *
 * Controls:
 *   ←/→  Switch view (long press for fast cycle)
 *   ↑/↓  Adjust value in Settings; tune frequency on Dashboard
 *   OK   Start/stop scanner; toggle RX on Dashboard
 *   Back Exit application
 */

#include "hackrf_companion.h"

/* ════════════════════════════════════════════════════════════
 *  Internal helpers
 * ════════════════════════════════════════════════════════════ */

/** Map an RSSI float value to a pixel bar width over [0, max_w]. */
static int rssi_to_bar(float rssi, int max_w) {
    if(rssi <= RSSI_FLOOR) return 0;
    if(rssi >= RSSI_CEIL) return max_w;
    float ratio = (rssi - RSSI_FLOOR) / (RSSI_CEIL - RSSI_FLOOR);
    return (int)(ratio * (float)max_w);
}

/** Map an RSSI float to a graph Y-coordinate within [graph_y, graph_y+graph_h]. */
static int rssi_to_y(float rssi, int graph_y, int graph_h) {
    if(rssi <= RSSI_FLOOR) return graph_y + graph_h;
    if(rssi >= RSSI_CEIL) return graph_y;
    float ratio = (rssi - RSSI_FLOOR) / (RSSI_CEIL - RSSI_FLOOR);
    return graph_y + graph_h - (int)(ratio * (float)graph_h);
}

/* ════════════════════════════════════════════════════════════
 *  Radio control (CC1101 via furi_hal_subghz)
 * ════════════════════════════════════════════════════════════ */

static bool radio_start(HackRFApp* app) {
    furi_hal_subghz_reset();
    furi_hal_subghz_load_preset(HACKRF_MOD_PRESETS[app->mod_idx]);

    uint32_t actual = furi_hal_subghz_set_frequency_and_path(
        HACKRF_FREQS[app->freq_idx].hz);
    if(actual == 0) {
        FURI_LOG_W(HACKRF_APP_TAG, "Freq not supported, using demo mode");
        return false;
    }

    furi_hal_subghz_rx();
    FURI_LOG_I(HACKRF_APP_TAG, "Radio RX started @ %lu Hz", actual);
    return true;
}

static void radio_stop(void) {
    furi_hal_subghz_idle();
    furi_hal_subghz_reset();
}

static float radio_read_rssi(bool radio_on) {
    if(!radio_on) {
        /* Demo-mode: return a plausible wandering value */
        static float demo = -85.0f;
        static int8_t dir = 1;
        demo += (float)dir * 0.8f;
        if(demo > -50.0f) dir = -1;
        if(demo < -110.0f) dir = 1;
        return demo;
    }
    return furi_hal_subghz_get_rssi();
}

/* Re-tune radio to a new frequency preset (called from settings). */
static void radio_retune(HackRFApp* app) {
    if(!app->radio_on) return;
    furi_hal_subghz_idle();
    furi_hal_subghz_load_preset(HACKRF_MOD_PRESETS[app->mod_idx]);
    furi_hal_subghz_set_frequency_and_path(HACKRF_FREQS[app->freq_idx].hz);
    furi_hal_subghz_rx();
}

/* ════════════════════════════════════════════════════════════
 *  Shared drawing helpers
 * ════════════════════════════════════════════════════════════ */

/** Draw the common header bar: title on left, "◄ ViewName n/N ►" on right. */
static void draw_header(Canvas* canvas, HackRFApp* app) {
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, HDR_H - 1, HACKRF_APP_TITLE);

    char nav[24];
    snprintf(nav, sizeof(nav), "< %s %d/%d >",
             HACKRF_VIEW_NAMES[app->view],
             (int)app->view + 1,
             (int)HackRFViewCount);
    /* Right-align: estimate 6px per character */
    int nav_x = SCR_W - (int)strlen(nav) * 6 - 1;
    if(nav_x < 0) nav_x = 0;
    canvas_draw_str(canvas, nav_x, HDR_H - 1, nav);

    canvas_draw_line(canvas, 0, HDR_H, SCR_W - 1, HDR_H);
}

/** Draw the common footer separator and hint text. */
static void draw_footer(Canvas* canvas, const char* hint) {
    canvas_draw_line(canvas, 0, FTR_Y - 1, SCR_W - 1, FTR_Y - 1);
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, SCR_H - 2, hint);
}

/* ════════════════════════════════════════════════════════════
 *  VIEW 1 – Dashboard
 * ════════════════════════════════════════════════════════════ */

static void render_dashboard(Canvas* canvas, HackRFApp* app) {
    /* Frequency */
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, CONT_Y + 8, "Freq:");
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 32, CONT_Y + 9, HACKRF_FREQS[app->freq_idx].label);

    /* RSSI bar */
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, CONT_Y + 21, "RSSI:");

    int bar_x = 32, bar_y = CONT_Y + 13, bar_w = 76, bar_h = 8;
    canvas_draw_frame(canvas, bar_x, bar_y, bar_w, bar_h);

    int fill = rssi_to_bar(app->rssi, bar_w - 2);
    if(fill > 0) {
        canvas_draw_box(canvas, bar_x + 1, bar_y + 1, fill, bar_h - 2);
    }

    /* Threshold tick mark */
    int thresh_x = bar_x + rssi_to_bar(SIGNAL_THRESHOLD, bar_w - 2);
    canvas_draw_line(canvas, thresh_x, bar_y - 1, thresh_x, bar_y + bar_h);

    /* dBm value */
    char rssi_str[16];
    snprintf(rssi_str, sizeof(rssi_str), "%.1f dBm", (double)app->rssi);
    canvas_draw_str(canvas, 111 - (int)strlen(rssi_str) * 5, CONT_Y + 21, rssi_str);

    /* Modulation & peak */
    char mod_peak[32];
    snprintf(mod_peak, sizeof(mod_peak), "Mod:%s  Peak:%.0f dBm",
             HACKRF_MOD_NAMES[app->mod_idx], (double)app->rssi_peak);
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, CONT_Y + 32, mod_peak);

    /* Signal status */
    if(app->signal_detected) {
        canvas_draw_str(canvas, 2, CONT_Y + 41, "* SIGNAL DETECTED *");
    } else {
        canvas_draw_str(canvas, 2, CONT_Y + 41, "Listening...");
    }

    draw_footer(canvas, "[OK]Toggle RX  [^v]Tune  [<>]View");
}

/* ════════════════════════════════════════════════════════════
 *  VIEW 2 – Frequency Scanner
 * ════════════════════════════════════════════════════════════ */

static void render_scanner(Canvas* canvas, HackRFApp* app) {
    canvas_set_font(canvas, FontSecondary);

    /* Band label and status */
    char hdr[40];
    snprintf(hdr, sizeof(hdr), "Band: %s  %s",
             HACKRF_BANDS[app->band_idx].label,
             app->scan_running ? "Scanning..." : "[OK] Start");
    canvas_draw_str(canvas, 2, CONT_Y + 8, hdr);

    /* Spectrum bars area: x=[2,125], y=[CONT_Y+10, FTR_Y-4] */
    int sx = 2, sy = CONT_Y + 10;
    int sw = SCAN_POINTS * 4;  /* 28 cols * 4 px wide each = 112 px */
    int sh = FTR_Y - 4 - sy;   /* ~31 px */

    /* Baseline */
    canvas_draw_line(canvas, sx, sy + sh, sx + sw, sy + sh);

    /* Bars */
    for(int i = 0; i < SCAN_POINTS; i++) {
        float v = app->scan_buf[i];
        int h = (sh * rssi_to_bar((int)v, 100)) / 100;
        if(h < 1) h = 1;
        int bx = sx + i * 4;
        /* Highlight scan cursor */
        if(app->scan_running && i == (int)app->scan_pos) {
            canvas_draw_frame(canvas, bx, sy + sh - h - 1, 3, h + 1);
        } else {
            canvas_draw_box(canvas, bx, sy + sh - h, 3, h);
        }
    }

    /* Current scan frequency under the cursor */
    if(app->scan_running) {
        uint32_t cur_hz = HACKRF_BANDS[app->band_idx].start_hz +
                          (uint32_t)app->scan_pos * app->scan_step_hz;
        char cur_str[32];
        snprintf(cur_str, sizeof(cur_str), "%.3f MHz  %.0f dBm",
                 (double)cur_hz / 1000000.0,
                 (double)app->rssi);
        canvas_draw_str(canvas, 2, CONT_Y + 8 + 10, cur_str);
    }

    draw_footer(canvas, "[OK]Scan  [^v]Band  [<>]View");
}

/* ════════════════════════════════════════════════════════════
 *  VIEW 3 – RSSI Monitor (scrolling graph)
 * ════════════════════════════════════════════════════════════ */

static void render_monitor(Canvas* canvas, HackRFApp* app) {
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, CONT_Y + 8, "RSSI History");

    /* Graph area */
    int gx = 14, gy = CONT_Y + 10;
    int gw = SCR_W - gx - 2;
    int gh = FTR_Y - 4 - gy; /* ~31 px */

    /* Axes */
    canvas_draw_line(canvas, gx, gy, gx, gy + gh);          /* Y axis */
    canvas_draw_line(canvas, gx, gy + gh, gx + gw, gy + gh); /* X axis */

    /* Y-axis labels */
    canvas_draw_str(canvas, 0, gy + 4, "-20");
    canvas_draw_str(canvas, 0, gy + gh / 2 + 2, "-70");
    canvas_draw_str(canvas, 0, gy + gh, "-120");

    /* Threshold horizontal dashed line */
    int thresh_y = rssi_to_y(SIGNAL_THRESHOLD, gy, gh);
    for(int x = gx + 2; x < gx + gw; x += 4) {
        canvas_draw_dot(canvas, x, thresh_y);
    }

    /* Plot history */
    if(app->hist_count > 1) {
        int count = (int)app->hist_count;
        int plot_w = gw - 2;
        for(int i = 1; i < count && i < plot_w; i++) {
            int idx_prev = ((int)app->hist_head - count + i - 1 + RSSI_HISTORY_LEN)
                           % RSSI_HISTORY_LEN;
            int idx_curr = ((int)app->hist_head - count + i + RSSI_HISTORY_LEN)
                           % RSSI_HISTORY_LEN;

            int x0 = gx + 1 + (i - 1) * plot_w / count;
            int x1 = gx + 1 + i * plot_w / count;
            int y0 = rssi_to_y(app->history[idx_prev], gy, gh);
            int y1 = rssi_to_y(app->history[idx_curr], gy, gh);

            canvas_draw_line(canvas, x0, y0, x1, y1);
        }
    }

    /* Stats bar */
    char stats[40];
    snprintf(stats, sizeof(stats), "Cur:%.0f  Peak:%.0f dBm",
             (double)app->rssi, (double)app->rssi_peak);
    canvas_draw_str(canvas, 2, FTR_Y - 4, stats);

    draw_footer(canvas, "[OK]Clear  [<>]View");
}

/* ════════════════════════════════════════════════════════════
 *  VIEW 4 – Settings
 * ════════════════════════════════════════════════════════════ */

static void render_settings(Canvas* canvas, HackRFApp* app) {
    canvas_set_font(canvas, FontSecondary);

    const char* items[3] = {"Frequency", "Modulation", "Scan Band"};
    const char* vals[3];

    vals[0] = HACKRF_FREQS[app->freq_idx].label;
    vals[1] = HACKRF_MOD_NAMES[app->mod_idx];
    vals[2] = HACKRF_BANDS[app->band_idx].label;

    for(int i = 0; i < 3; i++) {
        int row_y = CONT_Y + 10 + i * 13;

        if(i == (int)app->set_cursor) {
            /* Highlight selected row */
            canvas_draw_box(canvas, 0, row_y - 8, SCR_W, 10);
            canvas_set_color(canvas, ColorWhite);
        }

        canvas_draw_str(canvas, 3, row_y, items[i]);

        /* Value right-aligned */
        int vx = SCR_W - (int)strlen(vals[i]) * 6 - 4;
        if(vx < 60) vx = 60;
        canvas_draw_str(canvas, vx, row_y, vals[i]);

        if(i == (int)app->set_cursor) {
            canvas_set_color(canvas, ColorBlack);
        }
    }

    /* Radio status */
    char status[32];
    snprintf(status, sizeof(status), "Radio: %s", app->radio_on ? "ON (RX)" : "OFF");
    canvas_draw_str(canvas, 2, CONT_Y + 42, status);

    draw_footer(canvas, "[^v]Select  [<>]Adjust  [OK]Apply");
}

/* ════════════════════════════════════════════════════════════
 *  Master render callback (dispatches to active view)
 * ════════════════════════════════════════════════════════════ */

static void render_callback(Canvas* canvas, void* context) {
    HackRFApp* app = context;
    furi_assert(app);

    furi_mutex_acquire(app->mutex, FuriWaitForever);

    canvas_clear(canvas);
    draw_header(canvas, app);

    switch(app->view) {
    case HackRFViewDash:
        render_dashboard(canvas, app);
        break;
    case HackRFViewScan:
        render_scanner(canvas, app);
        break;
    case HackRFViewMon:
        render_monitor(canvas, app);
        break;
    case HackRFViewSet:
        render_settings(canvas, app);
        break;
    default:
        break;
    }

    furi_mutex_release(app->mutex);
}

/* ════════════════════════════════════════════════════════════
 *  Input callback – enqueue events for the main loop
 * ════════════════════════════════════════════════════════════ */

static void input_callback(InputEvent* event, void* context) {
    HackRFApp* app = context;
    furi_message_queue_put(app->event_queue, event, FuriWaitForever);
}

/* ════════════════════════════════════════════════════════════
 *  Settings: apply selected value changes
 * ════════════════════════════════════════════════════════════ */

static void settings_adjust(HackRFApp* app, int delta) {
    switch(app->set_cursor) {
    case 0: /* Frequency */
        app->freq_idx = (uint8_t)((app->freq_idx + HACKRF_FREQ_COUNT + delta)
                                  % HACKRF_FREQ_COUNT);
        radio_retune(app);
        break;
    case 1: /* Modulation */
        app->mod_idx = (uint8_t)((app->mod_idx + HackRFModCount + delta)
                                 % HackRFModCount);
        radio_retune(app);
        break;
    case 2: /* Scan band */
        app->band_idx = (uint8_t)((app->band_idx + HACKRF_BAND_COUNT + delta)
                                  % HACKRF_BAND_COUNT);
        break;
    default:
        break;
    }
}

/* ════════════════════════════════════════════════════════════
 *  Input processing
 * ════════════════════════════════════════════════════════════ */

static void process_input(HackRFApp* app, InputEvent* ev) {
    if(ev->type != InputTypeShort && ev->type != InputTypeRepeat) return;

    InputKey key = ev->key;

    /* Global: ← / → navigate views */
    if(key == InputKeyLeft || key == InputKeyRight) {
        int dir = (key == InputKeyRight) ? 1 : -1;
        app->view = (HackRFViewID)((app->view + HackRFViewCount + dir) % HackRFViewCount);
        return;
    }

    /* View-specific handling */
    switch(app->view) {

    /* ── Dashboard ─────────────────────────────────────── */
    case HackRFViewDash:
        if(key == InputKeyUp) {
            app->freq_idx = (uint8_t)((app->freq_idx + 1) % HACKRF_FREQ_COUNT);
            radio_retune(app);
        } else if(key == InputKeyDown) {
            app->freq_idx = (uint8_t)((app->freq_idx + HACKRF_FREQ_COUNT - 1)
                                      % HACKRF_FREQ_COUNT);
            radio_retune(app);
        } else if(key == InputKeyOk) {
            if(app->radio_on) {
                radio_stop();
                app->radio_on = false;
                FURI_LOG_I(HACKRF_APP_TAG, "Radio OFF");
            } else {
                app->radio_on = radio_start(app);
                FURI_LOG_I(HACKRF_APP_TAG, "Radio %s", app->radio_on ? "ON" : "demo");
            }
        }
        break;

    /* ── Scanner ────────────────────────────────────────── */
    case HackRFViewScan:
        if(key == InputKeyUp) {
            app->band_idx = (uint8_t)((app->band_idx + 1) % HACKRF_BAND_COUNT);
            app->scan_pos = 0;
            app->scan_running = false;
            memset(app->scan_buf, 0, sizeof(app->scan_buf));
        } else if(key == InputKeyDown) {
            app->band_idx = (uint8_t)((app->band_idx + HACKRF_BAND_COUNT - 1)
                                      % HACKRF_BAND_COUNT);
            app->scan_pos = 0;
            app->scan_running = false;
            memset(app->scan_buf, 0, sizeof(app->scan_buf));
        } else if(key == InputKeyOk) {
            if(!app->scan_running) {
                /* Start scan */
                app->scan_pos = 0;
                app->scan_step_hz =
                    (HACKRF_BANDS[app->band_idx].end_hz -
                     HACKRF_BANDS[app->band_idx].start_hz) /
                    SCAN_POINTS;
                memset(app->scan_buf, 0, sizeof(app->scan_buf));
                app->scan_running = true;
            } else {
                app->scan_running = false;
            }
        }
        break;

    /* ── Monitor ────────────────────────────────────────── */
    case HackRFViewMon:
        if(key == InputKeyOk) {
            /* Clear history */
            memset(app->history, 0, sizeof(app->history));
            app->hist_head = 0;
            app->hist_count = 0;
            app->rssi_peak = RSSI_FLOOR;
        }
        break;

    /* ── Settings ───────────────────────────────────────── */
    case HackRFViewSet:
        if(key == InputKeyUp) {
            app->set_cursor = (uint8_t)((app->set_cursor + 2) % 3);
        } else if(key == InputKeyDown) {
            app->set_cursor = (uint8_t)((app->set_cursor + 1) % 3);
        } else if(key == InputKeyRight) {
            settings_adjust(app, +1);
        } else if(key == InputKeyLeft) {
            settings_adjust(app, -1);
        } else if(key == InputKeyOk) {
            /* Re-apply current settings to radio */
            if(app->radio_on) {
                radio_retune(app);
            }
            notification_message(app->notifications, &sequence_success);
        }
        break;

    default:
        break;
    }
}

/* ════════════════════════════════════════════════════════════
 *  Timer callback – runs every UPDATE_PERIOD_MS ms
 *  Updates RSSI, scanner, history; triggers redraw.
 * ════════════════════════════════════════════════════════════ */

static void timer_callback(void* context) {
    HackRFApp* app = context;
    furi_assert(app);

    furi_mutex_acquire(app->mutex, FuriWaitForever);

    app->tick++;

    /* Read RSSI */
    float new_rssi = radio_read_rssi(app->radio_on);
    app->rssi = new_rssi;

    /* Update peak */
    if(new_rssi > app->rssi_peak) {
        app->rssi_peak = new_rssi;
    }

    /* Signal detection */
    bool was_detected = app->signal_detected;
    app->signal_detected = (new_rssi > SIGNAL_THRESHOLD);
    if(app->signal_detected && !was_detected) {
        notification_message(app->notifications, &sequence_blink_blue_10);
    }

    /* Push RSSI into history ring-buffer */
    app->history[app->hist_head] = new_rssi;
    app->hist_head = (uint8_t)((app->hist_head + 1) % RSSI_HISTORY_LEN);
    if(app->hist_count < RSSI_HISTORY_LEN) app->hist_count++;

    /* Advance scanner one step per tick (only on Scanner view) */
    if(app->scan_running && app->view == HackRFViewScan) {
        /* Tune to next scan frequency */
        uint32_t scan_hz = HACKRF_BANDS[app->band_idx].start_hz +
                           (uint32_t)app->scan_pos * app->scan_step_hz;

        if(app->radio_on) {
            furi_hal_subghz_idle();
            furi_hal_subghz_set_frequency_and_path(scan_hz);
            furi_hal_subghz_rx();
        }

        app->scan_buf[app->scan_pos] = new_rssi;
        app->scan_pos = (uint8_t)((app->scan_pos + 1) % SCAN_POINTS);
    }

    furi_mutex_release(app->mutex);

    /* Trigger viewport redraw from GUI thread */
    view_port_update(app->vp);
}

/* ════════════════════════════════════════════════════════════
 *  Allocation / free helpers
 * ════════════════════════════════════════════════════════════ */

static HackRFApp* app_alloc(void) {
    HackRFApp* app = malloc(sizeof(HackRFApp));
    furi_assert(app);
    memset(app, 0, sizeof(HackRFApp));

    app->view      = HackRFViewDash;
    app->running   = true;
    app->freq_idx  = 1;  /* default: 433.920 MHz */
    app->mod_idx   = HackRFModOOK;
    app->band_idx  = 1;  /* default: 433 MHz band */
    app->rssi      = RSSI_FLOOR;
    app->rssi_peak = RSSI_FLOOR;

    /* Pre-fill history with floor values */
    for(int i = 0; i < RSSI_HISTORY_LEN; i++) app->history[i] = RSSI_FLOOR;

    app->mutex       = furi_mutex_alloc(FuriMutexTypeNormal);
    app->event_queue = furi_message_queue_alloc(8, sizeof(InputEvent));

    app->gui           = furi_record_open(RECORD_GUI);
    app->notifications = furi_record_open(RECORD_NOTIFICATION);

    app->vp = view_port_alloc();
    view_port_draw_callback_set(app->vp, render_callback, app);
    view_port_input_callback_set(app->vp, input_callback, app);
    gui_add_view_port(app->gui, app->vp, GuiLayerFullscreen);

    app->timer = furi_timer_alloc(timer_callback, FuriTimerTypePeriodic, app);

    return app;
}

static void app_free(HackRFApp* app) {
    furi_assert(app);

    furi_timer_stop(app->timer);
    furi_timer_free(app->timer);

    gui_remove_view_port(app->gui, app->vp);
    view_port_free(app->vp);

    furi_record_close(RECORD_GUI);
    furi_record_close(RECORD_NOTIFICATION);

    furi_message_queue_free(app->event_queue);
    furi_mutex_free(app->mutex);

    free(app);
}

/* ════════════════════════════════════════════════════════════
 *  Application entry point
 * ════════════════════════════════════════════════════════════ */

int32_t hackrf_companion_app(void* p) {
    UNUSED(p);

    FURI_LOG_I(HACKRF_APP_TAG, "HackRF Companion v%s starting", HACKRF_APP_VERSION);

    HackRFApp* app = app_alloc();

    /* Attempt to start the CC1101 radio in RX mode */
    app->radio_on = radio_start(app);
    if(!app->radio_on) {
        FURI_LOG_W(HACKRF_APP_TAG, "Radio unavailable – running in demo mode");
        notification_message(app->notifications, &sequence_blink_yellow_10);
    } else {
        notification_message(app->notifications, &sequence_blink_green_10);
    }

    /* Start the periodic update timer */
    furi_timer_start(app->timer, furi_ms_to_ticks(UPDATE_PERIOD_MS));

    /* Main event loop */
    InputEvent ev;
    while(app->running) {
        FuriStatus status = furi_message_queue_get(app->event_queue, &ev, 200);

        if(status == FuriStatusOk) {
            furi_mutex_acquire(app->mutex, FuriWaitForever);

            if(ev.type == InputTypeShort && ev.key == InputKeyBack) {
                app->running = false;
            } else {
                process_input(app, &ev);
            }

            furi_mutex_release(app->mutex);
        }
    }

    /* Shutdown radio before exiting */
    if(app->radio_on) {
        radio_stop();
    }

    FURI_LOG_I(HACKRF_APP_TAG, "HackRF Companion exiting");
    app_free(app);
    return 0;
}
