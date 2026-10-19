"use client";

import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

export default function ProgressChart() {
  const data = {
    labels: ["W1", "W2", "W3", "W4", "W5", "W6"],
    datasets: [
      {
        label: "Mastery %",
        data: [42, 55, 61, 70, 78, 86],
        borderColor: "#3b6ef6",
        backgroundColor: "rgba(59,110,246,0.15)",
        tension: 0.35,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { min: 0, max: 100 } },
  };

  return <Line data={data} options={options} />;
}
