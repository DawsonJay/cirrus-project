export interface BaseOverlayProps {
  zIndex: number;
  opacity?: number;
  visible?: boolean;
  className?: string;
}

export interface OverlayData {
  id: string;
  name: string;
  type: string;
  data: any;
  zIndex: number;
  visible: boolean;
  opacity: number;
}

export interface OverlayManagerProps {
  children: React.ReactNode;
  className?: string;
}

export interface OverlayComponentProps extends BaseOverlayProps {
  data?: any;
  [key: string]: any;
}
