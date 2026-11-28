// Detect device theme preference

const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

// Temporary theme preference

let manualTheme = null;

// Get saved theme

function getSavedTheme() {
  if (manualTheme) {
    return manualTheme;
  }

  try {
    return localStorage.getItem("burnerTheme");
  } catch {
    return null;
  }
}

// Apply selected theme

function applyTheme(theme) {
  const isLight = theme === "light";

  document.documentElement.classList.toggle("light", isLight);

  const icon = document.getElementById("themeIcon");

  const text = document.getElementById("themeText");

  const button = document.getElementById("themeToggle");

  // Dynamically change sun and moon icon

  if (icon && text) {
    icon.textContent = isLight ? "☾" : "☀";

    text.textContent = isLight ? "Dark Mode" : "Light Mode";
  }

  if (button) {
    button.setAttribute(
      "aria-label",
      isLight ? "Switch to dark mode" : "Switch to light mode",
    );
  }
}

// Switch between dark and light mode

function toggleTheme() {
  const isLight = document.documentElement.classList.contains("light");

  const newTheme = isLight ? "dark" : "light";

  manualTheme = newTheme;

  applyTheme(newTheme);

  // Remember selected theme

  try {
    localStorage.setItem("burnerTheme", newTheme);
  } catch (error) {
    console.log("Theme preference could not be saved");
  }
}

// Automatically load theme

function loadTheme() {
  const savedTheme = getSavedTheme();

  if (savedTheme === "dark" || savedTheme === "light") {
    applyTheme(savedTheme);
  } else {
    applyTheme(systemTheme.matches ? "dark" : "light");
  }
}

// Load theme when page opens

loadTheme();

// Follow device theme changes
// if user has not manually selected a theme

systemTheme.addEventListener("change", function () {
  if (!getSavedTheme()) {
    loadTheme();
  }
});

// Synchronize theme across browser tabs

window.addEventListener("storage", function (event) {
  if (event.key === "burnerTheme") {
    manualTheme = null;

    loadTheme();
  }
});
