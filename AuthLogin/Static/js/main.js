// Script para el fondo dinámico que se mueve con el cursor
document.addEventListener("DOMContentLoaded", () => {
const background = document.querySelector(".background-animation")

if (background) {
    document.addEventListener("mousemove", (e) => {
      // Calcular la posición relativa del cursor
    const x = e.clientX / window.innerWidth
    const y = e.clientY / window.innerHeight

      // Mover el fondo en función de la posición del cursor
      background.style.backgroundPosition = `${x * 100}% ${y * 100}%`

      // Mover el gradiente radial
    const beforeElement = background.querySelector("::before")
    if (beforeElement) {
        beforeElement.style.transform = `translate(${x * 20}px, ${y * 20}px)`
    }
    })
}
})
