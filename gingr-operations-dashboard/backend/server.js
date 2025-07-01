import express from 'express';
import cors from 'cors';
import axios from 'axios';
import { config } from 'dotenv';

config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Gingr API configuration
const GINGR_BASE_URL = process.env.GINGR_BASE_URL; // e.g., https://yourapp.gingrapp.com
const GINGR_API_KEY = process.env.GINGR_API_KEY;

// Helper function to make Gingr API calls
const makeGingrRequest = async (endpoint, method = 'GET', data = {}) => {
  try {
    const config = {
      method,
      url: `${GINGR_BASE_URL}/api/v1${endpoint}`,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
      }
    };

    if (method === 'GET') {
      config.params = { key: GINGR_API_KEY, ...data };
    } else {
      const params = new URLSearchParams();
      params.append('key', GINGR_API_KEY);
      Object.keys(data).forEach(key => {
        params.append(key, data[key]);
      });
      config.data = params;
    }

    const response = await axios(config);
    return response.data;
  } catch (error) {
    console.error(`Error making Gingr API request to ${endpoint}:`, error.message);
    throw error;
  }
};

// API Routes

// Get today's dashboard summary
app.get('/api/dashboard/summary', async (req, res) => {
  try {
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
    
    const widgetData = await makeGingrRequest('/reservation_widget_data', 'GET', {
      timestamp: today
    });

    res.json({
      success: true,
      data: widgetData.data ?? widgetData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch dashboard summary',
      details: error.message
    });
  }
});

// Get today's reservations
app.get('/api/dashboard/reservations/today', async (req, res) => {
  try {
    const today = new Date().toISOString().split('T')[0];
    
    const reservations = await makeGingrRequest('/reservations', 'POST', {
      start_date: today,
      end_date: today
    });

    res.json({
      success: true,
      data: reservations.data ?? reservations
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch today\'s reservations',
      details: error.message
    });
  }
});

// Get currently checked in reservations
app.get('/api/dashboard/reservations/checked-in', async (req, res) => {
  try {
    const reservations = await makeGingrRequest('/reservations', 'POST', {
      checked_in: true
    });

    res.json({
      success: true,
      data: reservations.data ?? reservations
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch checked-in reservations',
      details: error.message
    });
  }
});

// Get back of house data (digital whiteboard)
app.get('/api/dashboard/back-of-house', async (req, res) => {
  try {
    const { location_id = 1, type_ids = '1,2,3,4,5' } = req.query;
    
    const backOfHouseData = await makeGingrRequest('/back_of_house', 'GET', {
      location_id,
      type_ids: type_ids.split(','),
      full_day: true
    });

    res.json({
      success: true,
      data: backOfHouseData.data ?? backOfHouseData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch back of house data',
      details: error.message
    });
  }
});

// Get reservation types
app.get('/api/dashboard/reservation-types', async (req, res) => {
  try {
    const reservationTypes = await makeGingrRequest('/reservation_types', 'GET', {
      active_only: true
    });

    res.json({
      success: true,
      data: reservationTypes.data ?? reservationTypes
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch reservation types',
      details: error.message
    });
  }
});

// Get locations
app.get('/api/dashboard/locations', async (req, res) => {
  try {
    const locations = await makeGingrRequest('/get_locations', 'GET');

    res.json({
      success: true,
      data: locations.data ?? locations
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch locations',
      details: error.message
    });
  }
});

// Get owner information
app.get('/api/dashboard/owner/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const owner = await makeGingrRequest('/owner', 'GET', { id });

    res.json({
      success: true,
      data: owner.data ?? owner
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch owner information',
      details: error.message
    });
  }
});

// Get all owners with enhanced data
app.get('/api/dashboard/owners', async (req, res) => {
  try {
    const { limit = 100, offset = 0, search = '' } = req.query;
    const owners = await makeGingrRequest('/owners', 'GET', {
      limit,
      offset,
      search
    });

    res.json({
      success: true,
      data: owners.data ?? owners
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch owners',
      details: error.message
    });
  }
});

// Get all animals with enhanced data
app.get('/api/dashboard/animals', async (req, res) => {
  try {
    const { limit = 100, offset = 0, search = '', vip_only = false } = req.query;
    const animals = await makeGingrRequest('/animals', 'GET', {
      limit,
      offset,
      search,
      vip_only
    });

    res.json({
      success: true,
      data: animals.data ?? animals
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch animals',
      details: error.message
    });
  }
});

// Get business intelligence metrics
app.get('/api/dashboard/analytics/business-intelligence', async (req, res) => {
  try {
    // Fetch multiple data sources in parallel
    const [owners, animals, reservationTypes] = await Promise.all([
      makeGingrRequest('/owners', 'GET', { limit: 1000 }),
      makeGingrRequest('/animals', 'GET', { limit: 1000 }),
      makeGingrRequest('/reservation_types', 'GET', { active_only: true })
    ]);

    // Extract actual data from responses to avoid double-nesting
    const ownersData = owners.data ?? owners;
    const animalsData = animals.data ?? animals;
    const reservationTypesData = reservationTypes.data ?? reservationTypes;
    
    // Calculate metrics
    const totalCustomers = ownersData?.length || 0;
    const totalPets = animalsData?.length || 0;
    const petsPerCustomer = totalCustomers > 0 ? (totalPets / totalCustomers).toFixed(2) : 0;
    
    // Analyze pet breeds
    const breedAnalysis = animalsData?.reduce((acc, animal) => {
      const breed = animal.breed || 'Unknown';
      acc[breed] = (acc[breed] || 0) + 1;
      return acc;
    }, {}) || {};

    // Analyze species distribution
    const speciesAnalysis = animalsData?.reduce((acc, animal) => {
      const species = animal.species || 'Unknown';
      acc[species] = (acc[species] || 0) + 1;
      return acc;
    }, {}) || {};

    // VIP pets count
    const vipPets = animalsData?.filter(animal => animal.vip === true)?.length || 0;

    // Calculate total customer balances
    const totalBalance = ownersData?.reduce((sum, owner) => {
      return sum + (parseFloat(owner.current_balance) || 0);
    }, 0) || 0;

    res.json({
      success: true,
      data: {
        overview: {
          totalCustomers,
          totalPets,
          petsPerCustomer: parseFloat(petsPerCustomer),
          vipPets,
          totalBalance: totalBalance.toFixed(2)
        },
        breedAnalysis,
        speciesAnalysis,
        serviceTypes: reservationTypesData || []
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch business intelligence data',
      details: error.message
    });
  }
});

// Get VIP pets and special needs alerts
app.get('/api/dashboard/alerts', async (req, res) => {
  try {
    const animals = await makeGingrRequest('/animals', 'GET', { limit: 1000 });
    const animalsData = animals.data ?? animals;
    
    const alerts = {
      vipPets: animalsData?.filter(animal => animal.vip === true) || [],
      specialNeeds: animalsData?.filter(animal => 
        animal.medicines?.length > 0 || 
        animal.allergies?.length > 0 || 
        animal.special_instructions
      ) || [],
      medicationRequired: animalsData?.filter(animal => animal.medicines?.length > 0) || []
    };

    res.json({
      success: true,
      data: alerts
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch alerts',
      details: error.message
    });
  }
});

// Search pets and owners
app.get('/api/dashboard/search', async (req, res) => {
  try {
    const { q: query, type = 'all' } = req.query;
    
    if (!query || query.length < 2) {
      return res.json({
        success: true,
        data: { owners: [], animals: [] }
      });
    }

    const results = {};
    
    if (type === 'all' || type === 'owners') {
      const owners = await makeGingrRequest('/owners', 'GET', {
        search: query,
        limit: 20
      });
      results.owners = owners.data ?? owners;
    }
    
    if (type === 'all' || type === 'animals') {
      const animals = await makeGingrRequest('/animals', 'GET', {
        search: query,
        limit: 20
      });
      results.animals = animals.data ?? animals;
    }

    res.json({
      success: true,
      data: results
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to perform search',
      details: error.message
    });
  }
});

// Get today's schedule with enhanced details
app.get('/api/dashboard/schedule/today', async (req, res) => {
  try {
    const today = new Date().toISOString().split('T')[0];
    
    // Get today's reservations and back of house data
    const [reservations, backOfHouse] = await Promise.all([
      makeGingrRequest('/reservations', 'POST', {
        start_date: today,
        end_date: today
      }),
      makeGingrRequest('/back_of_house', 'GET', {
        location_id: 1,
        type_ids: '1,2,3,4,5',
        full_day: true
      })
    ]);

    // Extract actual data from responses to avoid double-nesting
    const reservationsData = reservations.data ?? reservations;
    const backOfHouseData = backOfHouse.data ?? backOfHouse;

    // Combine and enhance the data
    const enhancedSchedule = {
      reservations: reservationsData || [],
      backOfHouse: backOfHouseData || [],
      summary: {
        totalReservations: reservationsData?.length || 0,
        checkedIn: reservationsData?.filter(r => r.checked_in)?.length || 0,
        pendingCheckIn: reservationsData?.filter(r => !r.checked_in && !r.checked_out)?.length || 0
      }
    };

    res.json({
      success: true,
      data: enhancedSchedule
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to fetch today\'s schedule',
      details: error.message
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: 'Gingr Operations Dashboard API is running',
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    success: false,
    error: 'Something went wrong!',
    details: err.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Gingr Operations Dashboard API running on port ${PORT}`);
  console.log(`📊 Dashboard API available at http://localhost:${PORT}/api`);
  
  if (!GINGR_BASE_URL || !GINGR_API_KEY) {
    console.warn('⚠️  WARNING: GINGR_BASE_URL and GINGR_API_KEY environment variables not set!');
    console.log('   Please create a .env file with your Gingr configuration.');
  }
});
