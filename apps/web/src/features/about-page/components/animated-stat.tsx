"use client";

import { useEffect, useMemo, useState } from "react";

type AnimatedStatProps = {
  value: string;
};

export function AnimatedStat({ value }: AnimatedStatProps) {
  const [displayValue, setDisplayValue] = useState(value);

  const parsedValue = useMemo(() => {
    const numericPart = Number.parseFloat(value.replace(/[^\d.]/g, ""));
    const prefix = value.match(/^[^\d]*/)?.[0] ?? "";
    const suffix = value.match(/[^\d.]+$/)?.[0] ?? "";

    return {
      numericPart,
      prefix,
      suffix,
      hasAnimation: Number.isFinite(numericPart) && !value.includes("/"),
      hasDecimal: value.includes("."),
    };
  }, [value]);

  useEffect(() => {
    if (!parsedValue.hasAnimation) {
      return;
    }

    let frameId = 0;
    const duration = 1400;
    const startedAt = performance.now();

    const render = (time: number) => {
      const progress = Math.min((time - startedAt) / duration, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const currentValue = parsedValue.numericPart * easedProgress;
      const formattedValue = parsedValue.hasDecimal
        ? currentValue.toFixed(1)
        : Math.round(currentValue).toString();

      setDisplayValue(
        `${parsedValue.prefix}${formattedValue}${parsedValue.suffix}`,
      );

      if (progress < 1) {
        frameId = window.requestAnimationFrame(render);
      }
    };

    frameId = window.requestAnimationFrame(render);

    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [parsedValue, value]);

  return <>{parsedValue.hasAnimation ? displayValue : value}</>;
}
