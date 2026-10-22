import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'IndiaTravelAgent — AI Travel Planner for India',
  description: 'Nationwide AI-powered travel agent and itinerary generator for all Indian states and union territories.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}
