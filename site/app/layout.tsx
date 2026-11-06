import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SINAG — John Ray Cacananta',
  description: 'A solar observatory for the engineering work of John Ray Cacananta.'
};

export const viewport: Viewport = { themeColor: '#090A0C' };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
