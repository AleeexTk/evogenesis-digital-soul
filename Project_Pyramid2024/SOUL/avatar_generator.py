import matplotlib.pyplot as plt
import numpy as np

# Создание сглаженного 2D-спрайта Архитектора
# Source: Architect.txt

# Создаем холст для спрайта с высоким разрешением
sprite_size = 256  # Увеличенное разрешение для сглаживания
avatar = np.zeros((sprite_size, sprite_size, 4))  # Альфа-канал для прозрачности

# Функция для рисования круга (например, голова)
def draw_circle(canvas, center, radius, color):
    y, x = np.ogrid[:canvas.shape[0], :canvas.shape[1]]
    mask = (x - center[0])**2 + (y - center[1])**2 <= radius**2
    canvas[mask] = color

# Функция для рисования прямоугольника (например, тело)
def draw_rectangle(canvas, top_left, bottom_right, color):
    canvas[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]] = color

# Голова (круг)
draw_circle(avatar, (128, 60), 40, (0.7, 0.7, 0.7, 1))  # Светло-серый

# Глаза (круги)
draw_circle(avatar, (118, 55), 8, (0, 1, 1, 1))  # Голубой левый глаз
draw_circle(avatar, (138, 55), 8, (0, 1, 1, 1))  # Голубой правый глаз

# Акцент (центр головы)
draw_circle(avatar, (128, 65), 6, (1, 0.84, 0, 1))  # Золотой акцент

# Тело (прямоугольник)
draw_rectangle(avatar, (108, 100), (148, 200), (0.5, 0.5, 0.5, 1))  # Серое тело

# Руки (прямоугольники)
draw_rectangle(avatar, (90, 120), (108, 160), (0.5, 0.5, 0.5, 1))  # Левая рука
draw_rectangle(avatar, (148, 120), (166, 160), (0.5, 0.5, 0.5, 1))  # Правая рука

# Ноги (прямоугольники)
draw_rectangle(avatar, (115, 200), (125, 240), (0.5, 0.5, 0.5, 1))  # Левая нога
draw_rectangle(avatar, (131, 200), (141, 240), (0.5, 0.5, 0.5, 1))  # Правая нога

# Отображение спрайта
fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(avatar)
ax.axis('off')
plt.title('Сглаженный 2D-Аватар Архитектора (256x256 пикселей)')
plt.savefig('avatar_architect_smooth.png', transparent=True)
print("Avatar saved as avatar_architect_smooth.png")
