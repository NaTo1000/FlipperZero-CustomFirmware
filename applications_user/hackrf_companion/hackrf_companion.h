#pragma once

/**
 * HackRF Companion - Flipper Zero SDR Control Panel
 *
 * Inspired by HackRF One SDR tool suite (hackrf-2026.01.3)
 * Reference: NetBSD pkgsrc/ham/hackrf
 *
 * Maps HackRF capabilities to the Flipper Zero CC1101 Sub-GHz radio:
 *   hackrf_biast       -> Gain / signal-boost control
 *   hackrf_clock       -> Frequency preset selection
 *   hackrf_transfer    -> RX monitor + RSSI capture
 *   hackrf_sweep       -> Frequency band scanner
 *
 * Target: Flipper Zero running Unleashed / Custom firmware
 */

#include <furi.h>
#include <furi_hal.h>
#include <gui/gui.h>
#include <input/input.h>
#include <notification/notification.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ── App identity ─────────────────────────────────────────── */
#define HACKRF_APP_TAG     "HackRF"
#define HACKRF_APP_VERSION "1.0.0"
#define HACKRF_APP_TITLE   "HackRF Companion"

/* ── Metric constants ─────────────────────────────────────── */
#define RSSI_HISTORY_LEN  56     /* samples kept for the monitor graph */
#define SCAN_POINTS       28     /* columns in the scanner spectrum    */
#define UPDATE_PERIOD_MS  100    /* timer tick / metric refresh rate   */
#define SIGNAL_THRESHOLD  -80.0f /* dBm – above this = signal detected */
#define RSSI_FLOOR        -120.0f
#define RSSI_CEIL         -20.0f

/* ── Screen geometry (128 × 64 px) ───────────────────────── */
#define SCR_W  128
#define SCR_H  64
#define HDR_H  12   /* header band height                         */
#define FTR_Y  55   /* footer top edge                            */
#define CONT_Y (HDR_H + 2) /* content area top                   */

/* ── Views ───────────────────────────────────────────────── */
typedef enum {
    HackRFViewDash = 0,
    HackRFViewScan,
    HackRFViewMon,
    HackRFViewSet,
    HackRFViewCount,
} HackRFViewID;

static const char* const HACKRF_VIEW_NAMES[HackRFViewCount] = {
    "Dashboard",
    "Scanner",
    "Monitor",
    "Settings",
};

/* ── Modulations ─────────────────────────────────────────── */
typedef enum {
    HackRFModOOK = 0,
    HackRFModFSK2,
    HackRFModGFSK,
    HackRFModCount,
} HackRFMod;

static const char* const HACKRF_MOD_NAMES[HackRFModCount] = {
    "OOK",
    "FSK2",
    "GFSK",
};

/* Corresponding furi_hal presets */
static const FuriHalSubGhzPreset HACKRF_MOD_PRESETS[HackRFModCount] = {
    FuriHalSubGhzPresetOok650Async,
    FuriHalSubGhzPreset2FSKDev476Async,
    FuriHalSubGhzPreset2FSKDev238Async,
};

/* ── Frequency presets (within CC1101 range) ─────────────── */
typedef struct {
    const char* label; /* display string, e.g. "433.920" */
    uint32_t    hz;
} HackRFFreqPreset;

static const HackRFFreqPreset HACKRF_FREQS[] = {
    {"315.000 MHz", 315000000UL},
    {"433.920 MHz", 433920000UL},
    {"868.350 MHz", 868350000UL},
    {"915.000 MHz", 915000000UL},
};
#define HACKRF_FREQ_COUNT ((int)(sizeof(HACKRF_FREQS) / sizeof(HACKRF_FREQS[0])))

/* ── Scan bands ───────────────────────────────────────────── */
typedef struct {
    const char* label;
    uint32_t    start_hz;
    uint32_t    end_hz;
} HackRFBand;

static const HackRFBand HACKRF_BANDS[] = {
    {"315 MHz", 314000000UL, 316000000UL},
    {"433 MHz", 432000000UL, 435000000UL},
    {"868 MHz", 866000000UL, 870000000UL},
    {"915 MHz", 913000000UL, 917000000UL},
};
#define HACKRF_BAND_COUNT ((int)(sizeof(HACKRF_BANDS) / sizeof(HACKRF_BANDS[0])))

/* ── Main application state ───────────────────────────────── */
typedef struct {
    /* Navigation */
    HackRFViewID view;
    bool         running;
    bool         radio_on;

    /* Radio configuration */
    uint8_t  freq_idx;   /* index into HACKRF_FREQS  */
    uint8_t  mod_idx;    /* index into HackRFMod     */
    uint8_t  band_idx;   /* index into HACKRF_BANDS  */

    /* Live metrics */
    float    rssi;
    float    rssi_peak;
    bool     signal_detected;

    /* RSSI history ring-buffer (for Monitor view) */
    float    history[RSSI_HISTORY_LEN];
    uint8_t  hist_head;
    uint8_t  hist_count;

    /* Scanner spectrum buffer */
    float    scan_buf[SCAN_POINTS];
    uint8_t  scan_pos;
    bool     scan_running;
    uint32_t scan_step_hz; /* frequency step per column */

    /* Settings cursor (0=freq, 1=mod, 2=band) */
    uint8_t set_cursor;

    /* RTOS / GUI handles */
    Gui*              gui;
    ViewPort*         vp;
    FuriMessageQueue* event_queue;
    NotificationApp*  notifications;
    FuriTimer*        timer;
    FuriMutex*        mutex;

    /* Tick counter for animations */
    uint32_t tick;
} HackRFApp;
