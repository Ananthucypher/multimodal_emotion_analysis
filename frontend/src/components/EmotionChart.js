import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

// Use the same emotion color mapping throughout your app
const emotionColors = {
  happy: "#10B981",
  sad: "#3B82F6",
  angry: "#EF4444",
  fear: "#8B5CF6",
  surprise: "#F59E0B",
  disgust: "#84CC16",
  neutral: "#6B7280"
};

const EmotionChart = ({ emotionData }) => {
  // emotionData expected as: { angry: 8, happy: 4, ... }

  const chartData = Object.entries(emotionData || {}).map(([name, value]) => ({
    name,
    value
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={3}
          dataKey="value"
          isAnimationActive={true}
        >
          {chartData.map((entry, idx) => (
            <Cell
              key={`cell-${idx}`}
              fill={emotionColors[entry.name.toLowerCase()] || "#C0C0C0"}
            />
          ))}
        </Pie>
        <Tooltip
          formatter={(value, name) =>
            [`${value}`, name.charAt(0).toUpperCase() + name.slice(1)]
          }
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default EmotionChart;
