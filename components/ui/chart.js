import { Chart as ChartJS, registerables } from "chart.js"

ChartJS.register(...registerables)

export const Chart = ChartJS