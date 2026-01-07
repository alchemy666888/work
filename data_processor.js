/**
 * BEFORE REFACTORING: Complex data processing function
 * This function has multiple responsibilities, nested conditionals,
 * and is difficult to understand and maintain.
 */

function processUserData(data, options) {
  let result = [];

  // Process each user
  for (let i = 0; i < data.length; i++) {
    let user = data[i];
    let processed = {};

    // Validate and process user data
    if (user && typeof user === 'object') {
      if (user.name && user.name.length > 0) {
        // Process name
        if (options && options.uppercase) {
          processed.name = user.name.toUpperCase();
        } else if (options && options.lowercase) {
          processed.name = user.name.toLowerCase();
        } else {
          processed.name = user.name;
        }

        // Process age
        if (user.age !== undefined && user.age !== null) {
          if (typeof user.age === 'string') {
            processed.age = parseInt(user.age, 10);
            if (isNaN(processed.age)) {
              processed.age = 0;
            }
          } else if (typeof user.age === 'number') {
            processed.age = user.age;
          } else {
            processed.age = 0;
          }

          // Calculate age category
          if (processed.age < 18) {
            processed.category = 'minor';
          } else if (processed.age >= 18 && processed.age < 65) {
            processed.category = 'adult';
          } else {
            processed.category = 'senior';
          }
        }

        // Process email
        if (user.email) {
          if (typeof user.email === 'string' && user.email.indexOf('@') > -1) {
            if (options && options.maskEmail) {
              let parts = user.email.split('@');
              if (parts[0].length > 2) {
                processed.email = parts[0].substring(0, 2) + '***@' + parts[1];
              } else {
                processed.email = '***@' + parts[1];
              }
            } else {
              processed.email = user.email.toLowerCase();
            }
          }
        }

        // Process address
        if (user.address) {
          processed.address = {};
          if (user.address.street) {
            processed.address.street = user.address.street;
          }
          if (user.address.city) {
            processed.address.city = user.address.city;
          }
          if (user.address.country) {
            if (options && options.countryCode) {
              // Simple country code mapping
              if (user.address.country === 'United States') {
                processed.address.country = 'US';
              } else if (user.address.country === 'United Kingdom') {
                processed.address.country = 'UK';
              } else if (user.address.country === 'Canada') {
                processed.address.country = 'CA';
              } else {
                processed.address.country = user.address.country;
              }
            } else {
              processed.address.country = user.address.country;
            }
          }
        }

        // Add to result if valid
        if (processed.name) {
          result.push(processed);
        }
      }
    }
  }

  // Sort results if requested
  if (options && options.sortBy) {
    if (options.sortBy === 'name') {
      result.sort(function(a, b) {
        if (a.name < b.name) return -1;
        if (a.name > b.name) return 1;
        return 0;
      });
    } else if (options.sortBy === 'age') {
      result.sort(function(a, b) {
        return (a.age || 0) - (b.age || 0);
      });
    }
  }

  return result;
}

module.exports = { processUserData };
