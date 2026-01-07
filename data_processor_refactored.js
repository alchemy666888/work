/**
 * AFTER REFACTORING: Clean, maintainable data processing
 * Separated concerns, reduced nesting, improved readability
 */

// Configuration constants
const AGE_CATEGORIES = {
  MINOR_MAX: 18,
  ADULT_MAX: 65,
};

const COUNTRY_CODES = {
  'United States': 'US',
  'United Kingdom': 'UK',
  'Canada': 'CA',
};

// Helper functions - each with a single responsibility

function isValidUser(user) {
  return user && typeof user === 'object' && user.name && user.name.length > 0;
}

function formatName(name, options = {}) {
  if (options.uppercase) {
    return name.toUpperCase();
  }
  if (options.lowercase) {
    return name.toLowerCase();
  }
  return name;
}

function parseAge(age) {
  if (age === undefined || age === null) {
    return null;
  }

  if (typeof age === 'number') {
    return age;
  }

  if (typeof age === 'string') {
    const parsed = parseInt(age, 10);
    return isNaN(parsed) ? 0 : parsed;
  }

  return 0;
}

function getAgeCategory(age) {
  if (age === null) {
    return undefined;
  }

  if (age < AGE_CATEGORIES.MINOR_MAX) {
    return 'minor';
  }

  if (age < AGE_CATEGORIES.ADULT_MAX) {
    return 'adult';
  }

  return 'senior';
}

function isValidEmail(email) {
  return typeof email === 'string' && email.indexOf('@') > -1;
}

function maskEmail(email) {
  const [localPart, domain] = email.split('@');
  const maskedLocal = localPart.length > 2
    ? localPart.substring(0, 2) + '***'
    : '***';
  return `${maskedLocal}@${domain}`;
}

function processEmail(email, options = {}) {
  if (!email || !isValidEmail(email)) {
    return undefined;
  }

  if (options.maskEmail) {
    return maskEmail(email);
  }

  return email.toLowerCase();
}

function convertCountryCode(country) {
  return COUNTRY_CODES[country] || country;
}

function processAddress(address, options = {}) {
  if (!address) {
    return undefined;
  }

  const processed = {};

  if (address.street) {
    processed.street = address.street;
  }

  if (address.city) {
    processed.city = address.city;
  }

  if (address.country) {
    processed.country = options.countryCode
      ? convertCountryCode(address.country)
      : address.country;
  }

  return Object.keys(processed).length > 0 ? processed : undefined;
}

function processUser(user, options = {}) {
  if (!isValidUser(user)) {
    return null;
  }

  const processed = {
    name: formatName(user.name, options),
  };

  const age = parseAge(user.age);
  if (age !== null) {
    processed.age = age;
    const category = getAgeCategory(age);
    if (category !== undefined) {
      processed.category = category;
    }
  }

  const email = processEmail(user.email, options);
  if (email !== undefined) {
    processed.email = email;
  }

  const address = processAddress(user.address, options);
  if (address !== undefined) {
    processed.address = address;
  }

  return processed;
}

function sortUsers(users, sortBy) {
  if (!sortBy) {
    return users;
  }

  const sortFunctions = {
    name: (a, b) => a.name.localeCompare(b.name),
    age: (a, b) => (a.age || 0) - (b.age || 0),
  };

  const sortFunction = sortFunctions[sortBy];
  if (!sortFunction) {
    return users;
  }

  return [...users].sort(sortFunction);
}

function processUserData(data, options = {}) {
  const processedUsers = data
    .map(user => processUser(user, options))
    .filter(user => user !== null);

  return sortUsers(processedUsers, options.sortBy);
}

module.exports = {
  processUserData,
  // Export helpers for testing
  isValidUser,
  formatName,
  parseAge,
  getAgeCategory,
  processEmail,
  processAddress,
  sortUsers,
};
