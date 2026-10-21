package com.x9.reader;

import android.app.Activity;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;

/**
 * Document reader for the X9 watch: a full-screen WebView over the converted HTML.
 * Scrolls by touch; the volume / d-pad / page keys scroll too (a side control, if the
 * watch has one, may map to them). The rotary crown is not delivered to apps on this
 * hardware, so in-app navigation uses touch and the on-screen contents button.
 */
public class MainActivity extends Activity {

    private static final int STEP = 110;

    private WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);     // table of contents + font buttons
        s.setDomStorageEnabled(true);     // remembers the chosen font size
        s.setDefaultTextEncodingName("utf-8");
        s.setBuiltInZoomControls(false);
        s.setSupportZoom(false);
        web.setVerticalScrollBarEnabled(true);
        web.setBackgroundColor(0xFF000000);
        web.loadUrl("file:///android_asset/doc.html");

        setContentView(web);
    }

    private boolean scroll(int dy) {
        if (web != null) {
            web.scrollBy(0, dy);
            return true;
        }
        return false;
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        int kc = e.getKeyCode();
        if (e.getAction() == KeyEvent.ACTION_DOWN) {
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

    @Override
    public boolean dispatchGenericMotionEvent(MotionEvent ev) {
        if (ev.getAction() == MotionEvent.ACTION_SCROLL) {
            float v = ev.getAxisValue(MotionEvent.AXIS_SCROLL);
            if (v == 0) {
                v = ev.getAxisValue(MotionEvent.AXIS_VSCROLL);
            }
            if (v != 0) {
                return scroll(Math.round(-v * STEP));
            }
        }
        return super.dispatchGenericMotionEvent(ev);
    }

    @Override
    public void onBackPressed() {
        finish();
    }
}
