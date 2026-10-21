package com.x9.reader;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.FrameLayout;
import android.widget.TextView;

/**
 * Document reader for the X9 watch: a full-screen WebView over the converted HTML.
 * Scrolls by touch, by the rotary crown, and by hardware keys (the crown on these
 * watches may be wired to volume / d-pad / page keys, so all are handled).
 *
 * The crown's actual event is unknown on this hardware, so a diagnostics strip is
 * built in: tap the bottom-left corner to toggle it, turn the crown, and it shows the
 * key code / motion axis values received. That tells us exactly what to bind.
 */
public class MainActivity extends Activity {

    private static final int STEP = 110;

    private WebView web;
    private TextView dbg;
    private final StringBuilder log = new StringBuilder();
    private int logLines = 0;

    private float downX, downY;
    private long downT;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        FrameLayout root = new FrameLayout(this);

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);     // TOC + font buttons
        s.setDomStorageEnabled(true);     // remembers chosen font size
        s.setDefaultTextEncodingName("utf-8");
        s.setBuiltInZoomControls(false);
        s.setSupportZoom(false);
        web.setVerticalScrollBarEnabled(true);
        web.setBackgroundColor(0xFF000000);
        web.loadUrl("file:///android_asset/doc.html");
        root.addView(web, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        dbg = new TextView(this);
        dbg.setBackgroundColor(0xDD000000);
        dbg.setTextColor(Color.WHITE);
        dbg.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        dbg.setPadding(12, 8, 12, 8);
        dbg.setText("диагностика ввода включена\nкрутите колёсико…");
        dbg.setVisibility(View.GONE);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.gravity = Gravity.BOTTOM;
        root.addView(dbg, lp);

        setContentView(root);
    }

    private boolean scroll(int dy) {
        if (web != null) {
            web.scrollBy(0, dy);
            return true;
        }
        return false;
    }

    private void record(String s) {
        if (logLines >= 6) {
            int nl = log.indexOf("\n");
            if (nl >= 0) {
                log.delete(0, nl + 1);
            }
            logLines--;
        }
        if (log.length() > 0) {
            log.append("\n");
        }
        log.append(s);
        logLines++;
        if (dbg != null) {
            dbg.setText(log.toString());
        }
    }

    // --- hardware keys: volume / d-pad / page -> scroll ---
    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        int kc = e.getKeyCode();
        if (e.getAction() == KeyEvent.ACTION_DOWN) {
            record("KEY " + kc + " (" + KeyEvent.keyCodeToString(kc) + ")");
            switch (kc) {
                case KeyEvent.KEYCODE_VOLUME_UP:
                case KeyEvent.KEYCODE_DPAD_UP:
                case KeyEvent.KEYCODE_PAGE_UP:
                    return scroll(-STEP * 3);
                case KeyEvent.KEYCODE_VOLUME_DOWN:
                case KeyEvent.KEYCODE_DPAD_DOWN:
                case KeyEvent.KEYCODE_PAGE_DOWN:
                    return scroll(STEP * 3);
                default:
                    break;
            }
        } else if (e.getAction() == KeyEvent.ACTION_UP) {
            switch (kc) {
                case KeyEvent.KEYCODE_VOLUME_UP:
                case KeyEvent.KEYCODE_VOLUME_DOWN:
                case KeyEvent.KEYCODE_DPAD_UP:
                case KeyEvent.KEYCODE_DPAD_DOWN:
                case KeyEvent.KEYCODE_PAGE_UP:
                case KeyEvent.KEYCODE_PAGE_DOWN:
                    return true;
                default:
                    break;
            }
        }
        return super.dispatchKeyEvent(e);
    }

    // --- rotary crown / mouse wheel -> scroll ---
    @Override
    public boolean dispatchGenericMotionEvent(MotionEvent ev) {
        if (ev.getAction() == MotionEvent.ACTION_SCROLL) {
            float sc = ev.getAxisValue(MotionEvent.AXIS_SCROLL);
            float vs = ev.getAxisValue(MotionEvent.AXIS_VSCROLL);
            float wh = ev.getAxisValue(MotionEvent.AXIS_WHEEL);
            record("MOTION src=" + ev.getSource()
                    + " scroll=" + sc + " vscroll=" + vs + " wheel=" + wh);
            float v = sc != 0 ? sc : (vs != 0 ? vs : wh);
            if (v != 0) {
                return scroll(Math.round(-v * STEP));
            }
        }
        return super.dispatchGenericMotionEvent(ev);
    }

    // --- bottom-left corner tap toggles the diagnostics strip ---
    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        if (ev.getAction() == MotionEvent.ACTION_DOWN) {
            downX = ev.getX();
            downY = ev.getY();
            downT = ev.getEventTime();
        } else if (ev.getAction() == MotionEvent.ACTION_UP) {
            View root = getWindow().getDecorView();
            boolean corner = downX < root.getWidth() * 0.28f
                    && downY > root.getHeight() * 0.78f;
            boolean tap = Math.abs(ev.getX() - downX) < 30
                    && Math.abs(ev.getY() - downY) < 30
                    && (ev.getEventTime() - downT) < 400;
            if (corner && tap) {
                dbg.setVisibility(dbg.getVisibility() == View.GONE ? View.VISIBLE : View.GONE);
                return true;
            }
        }
        return super.dispatchTouchEvent(ev);
    }

    @Override
    public void onBackPressed() {
        finish();
    }
}
