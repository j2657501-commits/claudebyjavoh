# THE LAST SECOND: промпты для фотореалистичной версии

Эти промпты нужны, чтобы заменить CG-планы на фотореалистичные клипы. Подходят Google Veo 3, OpenAI Sora, Kling 2.x и Runway Gen-4. Каждый план генерируй отдельно, в 16:9, 24 fps, в максимальном разрешении сервиса. Тайминг совпадает с CG-версией (`index.html`), поэтому звук и монтаж из неё подходят без изменений.

**Общий стиль (добавляй в конец каждого промпта):**
> shot on ARRI Alexa 65 with Panavision Sphero 65 lenses, IMAX 1.90:1 framing inside 16:9, photorealistic, natural skin texture with pores, physically accurate reflections and volumetric light, deep teal-and-amber color grade, subtle 35mm film grain, no text, no watermark, no CGI look

**Герой** (один и тот же во всех планах; к первому планы приложи референс-фото): мужчина около 35 лет, тёмные короткие волосы, щетина, длинное тёмно-серое шерстяное пальто, белая рубашка без галстука. Карие глаза с зелёными прожилками.

| # | Время | План | Промпт (EN) |
|---|---|---|---|
| 1 | 0.0–5.0 | Аэросъёмка | Hyperlapse-speed FPV drone dive at golden hour: the camera starts 800 m above a vast modern megacity, sun on the horizon at the end of a long avenue (Manhattanhenge effect), then plunges between glass skyscrapers, skimming facades that reflect the orange sky, down to street level of a huge scramble crossing packed with thousands of pedestrians, toward one man in a dark coat standing perfectly still in the middle of the moving crowd. Light rain catches the sun. |
| 2 | 5.0–6.8 | Остановка | Street-level slow dolly-in toward the still man in the dark coat at a crowded crossing at sunset, backlit by the low sun. In one instant the entire world freezes: pedestrians stop mid-step, a car is caught mid-air after a collision, raindrops hang motionless like glass crystals glinting in the sun, a flock of pigeons frozen between skyscrapers. Absolute stillness, only the camera keeps moving through the suspended raindrops. |
| 3 | 6.8–8.4 | Только глаза | Extreme macro close-up of the man's eye, brown iris with green flecks, realistic wet cornea reflecting the orange sunset street; everything is perfectly still except the eye, which darts left, then right, then looks straight into the lens. Shallow depth of field, eyelashes softly out of focus. |
| 4 | 8.4–11.0 | 360° | Slow 360-degree orbit around the man standing in a frozen city: glass shards from a shattered shop window, water droplets, a car and pedestrians all suspended in mid-air around him, sunset backlight with volumetric haze, bullet-time feel. |
| 5 | 11.0–16.4 | Небо трескается | Low-angle shot looking up past dark skyscrapers: the sunset sky begins to crack like a giant mirror, white-hot fracture lines spread across it, and pieces of sky fall away revealing an infinite starfield and purple nebulae behind; tiny glass shards float in the foreground. |
| 6 | 16.4–19.5 | Океан | Top-down crane shot: the asphalt under the man's feet turns into a crystal-clear ocean spreading outward in a glowing ring; frozen pedestrians now stand on the water surface, caustic light dancing beneath. |
| 7 | 19.5–22.3 | Город сгибается | Wide shot: the whole city bends upward and folds over the sky like a rolling wave, skyscrapers curving impossibly, the avenue rising into the cosmos above, Inception-style; the man is a tiny figure on the water. |
| 8 | 22.3–23.0 | Нырок | The camera dives straight down into the water, plunging underwater through bubbles and light rays into darkness. |
| 9 | 23.0–30.0 | Чёрная дыра | Out of the darkness into open space: planet Earth curves below, and above it a colossal black hole with a glowing accretion disk bent by gravitational lensing (Interstellar style) tears clouds and continents off the Earth into spiraling streams of light. Slow push-in. |
| 10 | 30.0–33.0 | Старый он | Inside the black hole's shadow, the reflection of the same man appears, but very old: white hair, deeply wrinkled skin, slightly hunched, the same dark coat. He slowly raises his hand toward the camera. |
| 11 | 33.0–34.4 | Схлопывание | The entire universe (stars, the accretion disk, the Earth) collapses inward into a single small glowing sphere of white-gold light. |
| 12 | 34.4–38.8 | Глаз | Start inside the pupil, where a whole galaxy is reflected, then pull back to an extreme macro of the man's eye; hold, then he blinks slowly and everything cuts to black. |

Титр 38.85–43 с: «ВРЕМЯ НИКОГДА НЕ ОСТАНАВЛИВАЛОСЬ. / ЭТО ТЫ ЗАКОНЧИЛСЯ.» (PT Serif, разрядка 0.32em, по центру).

**Советы:**
- Планы 3 и 12 — один и тот же глаз. Генерируй их с одним референсом, чтобы радужка совпала.
- Если сервис поддерживает первый и последний кадр (Kling, Runway, Veo), задай последний кадр плана N первым кадром плана N+1. Так получатся бесшовные переходы: дождь, вода, тьма, сфера, зрачок.
- Звук не генерируй: готовая партитура и SFX лежат в `audio.wav`, синхронно с таймингом выше.
