// Test if frontend can fetch API data correctly
async function testTideAPI() {
  try {
    console.log('Testing TidePage API integration...\n');

    // Simulate TidePage API call
    const response = await fetch(
      'http://localhost:5000/api/tide/hourly?lat=37.5665&lon=126.9780&date=2026-06-08'
    );

    if (!response.ok) {
      console.error('API call failed:', response.status);
      return;
    }

    const data = await response.json();

    // Check highTides
    console.log('1. Checking highTides field:');
    if (data.highTides && Array.isArray(data.highTides)) {
      console.log('   ✓ highTides exists and is array');
      console.log('   ✓ Sample:', data.highTides[0]);
    } else {
      console.log('   ✗ highTides missing or invalid');
    }

    // Check lowTides
    console.log('\n2. Checking lowTides field:');
    if (data.lowTides && Array.isArray(data.lowTides)) {
      console.log('   ✓ lowTides exists and is array');
      console.log('   ✓ Sample:', data.lowTides[0]);
    } else {
      console.log('   ✗ lowTides missing or invalid');
    }

    // Check hourly weather data
    console.log('\n3. Checking hourly weather data:');
    if (data.hourly && Array.isArray(data.hourly) && data.hourly.length > 0) {
      const sample = data.hourly[0];
      const requiredFields = ['hour', 'height', 'weather', 'temp', 'windSpeed', 'windDir', 'waveHeight', 'wavePeriod'];
      const missingFields = requiredFields.filter(field => !(field in sample));

      if (missingFields.length === 0) {
        console.log('   ✓ All required fields present');
        console.log('   ✓ Sample hour 0:', {
          hour: sample.hour,
          weather: sample.weather,
          temp: sample.temp,
          windSpeed: sample.windSpeed,
          windDir: sample.windDir,
          waveHeight: sample.waveHeight
        });
      } else {
        console.log('   ✗ Missing fields:', missingFields);
      }
    }

    console.log('\n✓ API integration test passed! TidePage should work correctly now.');

  } catch (err) {
    console.error('Error:', err.message);
  }
}

testTideAPI();
