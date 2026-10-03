"""앱 아이콘(PNG)을 만든다 -> icons/ (GitHub 페이지 맨 위 폴더). 모양을 바꿀 때만 다시 실행."""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "icons")
NAVY, INK, WHITE, ORANGE = (30, 62, 120), (20, 35, 61), (255, 255, 255), (217, 72, 15)
SS = 4  # 4배 크게 그린 뒤 줄여서 모서리를 부드럽게


def draw(size, safe):
    """safe=True면 가장자리에서 안쪽으로 모은 그림(마스크형 아이콘용). 배경은 전체를 채운다."""
    n = size * SS
    img = Image.new("RGB", (n, n), NAVY)
    d = ImageDraw.Draw(img)
    s = 0.62 if safe else 0.74  # 그림이 차지하는 비율
    w = int(n * s)
    x0 = (n - w) // 2
    y0 = (n - w) // 2 + int(n * 0.01)
    r = int(w * 0.13)
    # 달력 몸통
    d.rounded_rectangle([x0, y0, x0 + w, y0 + w], radius=r, fill=WHITE)
    # 달력 머리띠
    head = int(w * 0.26)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + head + r], radius=r, fill=INK)
    d.rectangle([x0, y0 + head, x0 + w, y0 + head + r], fill=WHITE)
    # 고리
    for fx in (0.28, 0.72):
        cx = x0 + int(w * fx)
        d.rounded_rectangle([cx - int(w * 0.035), y0 - int(w * 0.07), cx + int(w * 0.035), y0 + int(w * 0.11)],
                            radius=int(w * 0.035), fill=ORANGE)
    # 날짜 점 3x2, 하나는 강조
    gx0, gy0 = x0 + int(w * 0.17), y0 + int(w * 0.46)
    step_x, step_y, dr = int(w * 0.25), int(w * 0.21), int(w * 0.065)
    for row in range(2):
        for col in range(3):
            cx, cy = gx0 + col * step_x + dr, gy0 + row * step_y + dr
            hot = (row, col) == (0, 1)
            d.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=ORANGE if hot else (176, 193, 222))
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, size, safe in [("icon-192.png", 192, False), ("icon-512.png", 512, False),
                             ("maskable-512.png", 512, True), ("apple-touch-180.png", 180, False)]:
        draw(size, safe).save(os.path.join(OUT, name))
        print("저장:", os.path.join("icons", name))


if __name__ == "__main__":
    main()
