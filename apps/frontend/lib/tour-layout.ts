// Geometry adapted from the inspected Roomedy tour; no sibling state or styling.
export type TourRect = {
  left: number;
  top: number;
  right: number;
  bottom: number;
};
export type TourViewport = {
  left: number;
  top: number;
  width: number;
  height: number;
};
export type TourBox = {
  left: number;
  top: number;
  width: number;
  height: number;
};
export const TOUR_FADE_MS = 180;
export function sameTourBox(a: TourBox, b: TourBox) {
  return (['left', 'top', 'width', 'height'] as const).every(
    (key) => Math.abs(a[key] - b[key]) < 0.5,
  );
}
export function tourSpotlight(rect: TourRect, view: TourViewport): TourBox {
  const left = Math.min(
      view.left + view.width,
      Math.max(view.left, rect.left - 6),
    ),
    top = Math.min(view.top + view.height, Math.max(view.top, rect.top - 6));
  return {
    left,
    top,
    width: Math.max(0, Math.min(rect.right + 6, view.left + view.width) - left),
    height: Math.max(
      0,
      Math.min(rect.bottom + 6, view.top + view.height) - top,
    ),
  };
}
export function tourPanels(
  hole: TourBox | null,
  view: TourViewport,
): TourBox[] {
  if (!hole) return [{ ...view }];
  return [
    {
      left: view.left,
      top: view.top,
      width: view.width,
      height: hole.top - view.top,
    },
    {
      left: view.left,
      top: hole.top,
      width: hole.left - view.left,
      height: hole.height,
    },
    {
      left: hole.left + hole.width,
      top: hole.top,
      width: view.left + view.width - hole.left - hole.width,
      height: hole.height,
    },
    {
      left: view.left,
      top: hole.top + hole.height,
      width: view.width,
      height: view.top + view.height - hole.top - hole.height,
    },
  ];
}
/** Measure text first; prefer a free side, then clamp to the real visible viewport. */
export function tourPlacement(
  target: TourRect | null,
  view: TourViewport,
  measuredHeight: number,
): TourBox {
  const margin = Math.min(16, view.width / 4, view.height / 4),
    width = Math.max(1, Math.min(348, view.width - margin * 2)),
    height = Math.max(1, Math.min(measuredHeight, view.height - margin * 2));
  const boundX = (x: number) =>
    Math.max(
      view.left + margin,
      Math.min(x, view.left + view.width - margin - width),
    );
  const boundY = (y: number) =>
    Math.max(
      view.top + margin,
      Math.min(y, view.top + view.height - margin - height),
    );
  if (!target)
    return {
      left: boundX(view.left + (view.width - width) / 2),
      top: boundY(view.top + (view.height - height) / 2),
      width,
      height,
    };
  const below = target.bottom + 14,
    above = target.top - height - 14;
  let left = boundX(target.left),
    top = below;
  if (below + height > view.top + view.height - margin) {
    if (above >= view.top + margin) top = above;
    else if (target.right + 14 + width <= view.left + view.width - margin) {
      left = target.right + 14;
      top = target.top;
    } else if (target.left - width - 14 >= view.left + margin) {
      left = target.left - width - 14;
      top = target.top;
    } else top = view.top + view.height - height - margin;
  }
  return { left: boundX(left), top: boundY(top), width, height };
}
