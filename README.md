
# Affiliate Marketing Platform API

A Django REST Framework-based affiliate marketing platform that allows merchants to manage products and affiliates to earn commissions through tracking links.

## Features

- **User Management**: Role-based authentication (Merchants & Affiliates)
- **Product Management**: CRUD operations for products and categories
- **Affiliate Tracking**: Generate and manage tracking links
- **Click Analytics**: Track clicks, conversions, and user engagement
- **RESTful API**: Comprehensive API with JWT authentication

## Key Features

### Tracking System

- Generate unique tracking links for products
- Track clicks with detailed analytics
- Monitor conversion rates
- View real-time statistics
- Filter analytics by date range

### Security

- JWT authentication
- Role-based access control
- Secure token refresh
- Rate limiting

## Requirements

- Python 3.8+
- Django 4.2+
- Django REST Framework
- PostgreSQL (recommended) or SQLite
- Redis (for caching)


## Installation

```bash
# Clone the repository
git clone https://github.com/Sreyas62/AffiHub
cd AffiHub

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver


## API Endpoints

### Authentication
- `POST /api/auth/login/` - Get JWT tokens
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/verify/` - Verify token

### Users
- `POST /api/users/` - Register a new user
- `GET /api/users/me/` - Get current user\'s profile
- `PUT /api/users/{id}/` - Update user profile (owner only)
- `PATCH /api/users/{id}/` - Partially update user profile (owner only)
- `DELETE /api/users/{id}/` - Delete user account (owner only)
- `POST /api/users/login/` - Login and get JWT tokens
- `POST /api/users/logout/` - Logout (blacklist refresh token)
- `POST /api/users/change_password/` - Change user password
- `GET /api/users/` - List all users (admin only)
- `GET /api/users/affiliates/` - List all affiliates
- `GET /api/users/merchants/` - List all merchants

### Tracking
- `GET /api/tracking/links/` - List tracking links (Admin)
- `POST /api/tracking/links/` - Create tracking link
- `GET /api/tracking/links/me/` - Get my tracking links
- `GET /api/tracking/click/{code}/` - Track click (public)
- `GET /api/tracking/clicks/` - View click analytics
- `POST /api/tracking/conversions/` - Record conversion
- `GET /api/tracking/conversions/` - View conversion analytics

### Products
- `GET /api/products/` - List products
- `POST /api/products/` - Create product (Merchant)
- `GET /api/products/{id}/` - Get product details
- `PUT/PATCH /api/products/{id}/` - Update product
- `DELETE /api/products/{id}/` - Delete product

## Environment Variables

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/affiliate_db
REDIS_URL=redis://localhost:6379/0
```


## To implement and Future Scope

- Commision system
- Payment Integration
- Frontend development and Integration


## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

