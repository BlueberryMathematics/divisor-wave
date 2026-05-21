/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow loading local file:// images when running as packaged Electron app
  images: { unoptimized: true },
}

module.exports = nextConfig
