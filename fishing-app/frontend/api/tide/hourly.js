export default async function handler(req, res) {
  const { date, lat, lon } = req.query;

  // 환경 변수에서 백엔드 URL 가져오기 (Vercel 배포 후 설정)
  const backendUrl = process.env.VITE_API_URL || 'http://localhost:8000';

  try {
    const url = new URL('/api/tide/hourly', backendUrl);
    url.searchParams.append('date', date);
    url.searchParams.append('lat', lat);
    url.searchParams.append('lon', lon);

    const response = await fetch(url.toString());

    if (!response.ok) {
      return res.status(response.status).json({
        error: `Backend returned ${response.status}`
      });
    }

    const data = await response.json();
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
    res.status(200).json(data);
  } catch (error) {
    console.error('Tide API proxy error:', error);
    res.status(500).json({
      error: 'API proxy failed',
      backend: backendUrl,
      details: error.message
    });
  }
}
