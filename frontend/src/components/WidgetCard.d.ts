import type { ReactNode } from "react";

interface WidgetCardProps {
  title?: string;
  titleExtra?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export default function WidgetCard(props: WidgetCardProps): JSX.Element;
