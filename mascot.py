"""Reusable Jumbo mascot component.

Renders one of Jumbo's mp4 animations, optionally with a speech
bubble, using streamlit.components.v1.html. The mp4 files live in
static/jumbo/ and are served through raw.githubusercontent.com
because Streamlit's HTML component runs in a sandboxed iframe that
cannot see local project files directly.

The source mp4s have a solid white background baked into their
pixels (video doesn't support real transparency the way PNG does).
When circular=False, we can't just hide it with CSS, so instead we
draw each video frame onto a hidden <canvas> and make near-white
pixels transparent in real time ("chroma-key"), then show the
canvas instead of the raw video. circular=True (used on Ask Jumbo)
keeps the original plain <video> + circular frame, untouched.

Layout: circular=True keeps Jumbo and the speech bubble side by
side (Ask Jumbo page, unchanged). circular=False stacks Jumbo on
top and the speech bubble below, and the bubble text wraps freely
across multiple lines instead of forcing one long line.

Usage:
    from mascot import show_mascot

    show_mascot("wave", "Hi Akash, great to have you back.")
    show_mascot("wave", show_bubble=False, size=240)
    show_mascot("wave", "Hi!", circular=False)  # stacked, no circle
"""

import uuid as _uuid

import streamlit.components.v1 as components

GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/achakravorty1804/jumbo-ai/main/static/jumbo"
)

MASCOT_FILES = {
    "wave": "jumbo_wave.mp4",
    "thinking": "jumbo_thinking.mp4",
    "thumbsup": "jumbo_thumbsup.mp4",
    "dejected": "jumbo_dejected.mp4",
    "clapping": "jumbo_clapping.mp4",
    "showing": "jumbo_showing.mp4",
}

COLOR_BUBBLE_BG = "#FFFFFF"
COLOR_BUBBLE_BORDER = "#FFC6DE"
COLOR_ACCENT_BLUE = "#CDEBFB"
COLOR_TEXT = "#3A3A3A"

WHITE_THRESHOLD = 235

_CANVAS_SCRIPT_TEMPLATE = """
<video
    id="jvid_$UID$"
    src="$VIDEO_URL$"
    autoplay
    muted
    playsinline
    loop
    crossorigin="anonymous"
    style="display:none;"
></video>
<canvas
    id="jcanvas_$UID$"
    style="width: $SIZE$px; height: auto; flex-shrink: 0; display:block; background: transparent;"
></canvas>
<script>
(function() {
    var video = document.getElementById("jvid_$UID$");
    var canvas = document.getElementById("jcanvas_$UID$");
    var ctx = canvas.getContext("2d", { willReadFrequently: true });
    var threshold = $THRESHOLD$;
    var failed = false;

    function draw() {
        if (failed) return;

        if (video.readyState >= 2 && video.videoWidth > 0) {
            if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
            }
            try {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                var frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
                var data = frame.data;
                for (var i = 0; i < data.length; i += 4) {
                    if (data[i] > threshold && data[i + 1] > threshold && data[i + 2] > threshold) {
                        data[i + 3] = 0;
                    }
                }
                ctx.putImageData(frame, 0, 0);
            } catch (e) {
                failed = true;
                video.style.display = "block";
                canvas.style.display = "none";
                return;
            }
        }
        requestAnimationFrame(draw);
    }

    video.play().catch(function() {});
    requestAnimationFrame(draw);
})();
</script>
"""


def _canvas_video_tag(video_url, size):
    uid = _uuid.uuid4().hex[:8]
    return (
        _CANVAS_SCRIPT_TEMPLATE
        .replace("$UID$", uid)
        .replace("$VIDEO_URL$", video_url)
        .replace("$SIZE$", str(size))
        .replace("$THRESHOLD$", str(WHITE_THRESHOLD))
    )


def show_mascot(state, message="", height=None, show_bubble=True, size=300, circular=True):
    """Render Jumbo's mascot animation, with an optional speech bubble.

    state: one of "wave", "thinking", "thumbsup", "dejected", "clapping"
    message: text Jumbo "says" (ignored if show_bubble is False)
    height: pixel height of the component (auto if not given)
    show_bubble: whether to render the speech bubble
    size: width in pixels of Jumbo's video
    circular: True (default) = circular white-ringed frame, video and
        bubble side by side, exactly as before (Ask Jumbo page --
        do not change its calls). False = no circle/border, white
        background keyed out via canvas, video stacked on top with
        the bubble wrapping freely underneath.
    """
    filename = MASCOT_FILES.get(state, MASCOT_FILES["wave"])
    video_url = f"{GITHUB_RAW_BASE}/{filename}"

    if circular:
        if height is None:
            height = size + 40

        video_style = f"""
                width: {size}px;
                height: {size}px;
                border-radius: 50%;
                object-fit: cover;
                border: 5px solid {COLOR_ACCENT_BLUE};
                background: {COLOR_ACCENT_BLUE};
                flex-shrink: 0;
                box-shadow: 0 4px 14px rgba(0,0,0,0.12);
        """
        video_tag = f"""
        <video
            src="{video_url}"
            autoplay
            muted
            playsinline
            style="{video_style}"
        ></video>
        """

        if not show_bubble:
            html = f"""
            <div style="display:flex; justify-content:center; align-items:center; padding:4px;">
                {video_tag}
            </div>
            """
            components.html(html, height=height)
            return

        html = f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 20px;
            font-family: 'Source Sans Pro', sans-serif;
            padding: 6px 4px;
        ">
            {video_tag}
            <div style="
                position: relative;
                background: {COLOR_BUBBLE_BG};
                border: 2px solid {COLOR_BUBBLE_BORDER};
                border-radius: 20px;
                padding: 16px 20px;
                max-width: 460px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            ">
                <div style="
                    position: absolute;
                    left: -12px;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 0;
                    height: 0;
                    border-top: 12px solid transparent;
                    border-bottom: 12px solid transparent;
                    border-right: 14px solid {COLOR_BUBBLE_BORDER};
                "></div>
                <div style="
                    position: absolute;
                    left: -9px;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 0;
                    height: 0;
                    border-top: 11px solid transparent;
                    border-bottom: 11px solid transparent;
                    border-right: 13px solid {COLOR_BUBBLE_BG};
                "></div>
                <p style="
                    margin: 0;
                    color: {COLOR_TEXT};
                    font-size: 17px;
                    line-height: 1.45;
                ">{message}</p>
            </div>
        </div>
        """
        components.html(html, height=height)
        return

    # circular=False: stacked layout, video keyed via canvas
    video_tag = _canvas_video_tag(video_url, size)

    if not show_bubble:
        if height is None:
            height = size + 40
        html = f"""
        <div style="display:flex; justify-content:center; align-items:center; padding:4px;">
            {video_tag}
        </div>
        """
        components.html(html, height=height)
        return

    if height is None:
        height = size + 170

    bubble_max_width = max(size + 160, 260)

    html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        font-family: 'Source Sans Pro', sans-serif;
        padding: 6px 4px;
        text-align: center;
    ">
        {video_tag}
        <div style="
            position: relative;
            background: {COLOR_BUBBLE_BG};
            border: 2px solid {COLOR_BUBBLE_BORDER};
            border-radius: 20px;
            padding: 14px 20px;
            max-width: {bubble_max_width}px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-top: 8px;
        ">
            <div style="
                position: absolute;
                top: -10px;
                left: 50%;
                transform: translateX(-50%);
                width: 0;
                height: 0;
                border-left: 10px solid transparent;
                border-right: 10px solid transparent;
                border-bottom: 12px solid {COLOR_BUBBLE_BORDER};
            "></div>
            <div style="
                position: absolute;
                top: -7px;
                left: 50%;
                transform: translateX(-50%);
                width: 0;
                height: 0;
                border-left: 9px solid transparent;
                border-right: 9px solid transparent;
                border-bottom: 11px solid {COLOR_BUBBLE_BG};
            "></div>
            <p style="
                margin: 0;
                color: {COLOR_TEXT};
                font-size: 16px;
                line-height: 1.45;
                white-space: normal;
                word-wrap: break-word;
            ">{message}</p>
        </div>
    </div>
    """
    components.html(html, height=height)