// FurrOS: default wallpaper and launcher icon for every new Plasma user
const wallpaper = "file:///usr/share/backgrounds/furros/current.png";

for (const d of desktops()) {
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", wallpaper);
    d.writeConfig("FillMode", "2");
}

for (const p of panels()) {
    for (const w of p.widgets()) {
        if (w.type === "org.kde.plasma.kickoff" || w.type === "org.kde.plasma.kicker") {
            w.currentConfigGroup = ["General"];
            w.writeConfig("icon", "furros");
        }
    }
}
