/**
 * Tests to verify refactored code maintains the same behavior
 */

const { processUserData: processOriginal } = require('./data_processor');
const { processUserData: processRefactored } = require('./data_processor_refactored');

function assertEqual(actual, expected, testName) {
  const actualStr = JSON.stringify(actual, null, 2);
  const expectedStr = JSON.stringify(expected, null, 2);

  if (actualStr === expectedStr) {
    console.log(`✓ ${testName}`);
    return true;
  } else {
    console.error(`✗ ${testName}`);
    console.error('Expected:', expectedStr);
    console.error('Actual:', actualStr);
    return false;
  }
}

function runTests() {
  console.log('Running tests to verify refactored code maintains same behavior...\n');

  let passed = 0;
  let failed = 0;

  // Test data
  const testData = [
    {
      name: 'John Doe',
      age: 30,
      email: 'john@example.com',
      address: {
        street: '123 Main St',
        city: 'New York',
        country: 'United States',
      },
    },
    {
      name: 'Jane Smith',
      age: '25',
      email: 'jane@example.com',
      address: {
        city: 'London',
        country: 'United Kingdom',
      },
    },
    {
      name: 'Bob Johnson',
      age: 70,
      email: 'bob@example.com',
    },
    {
      name: 'Alice Williams',
      age: 15,
      email: 'alice@example.com',
      address: {
        country: 'Canada',
      },
    },
    {
      name: 'Invalid User',
      age: 'not a number',
      email: 'invalid-email',
    },
  ];

  // Test 1: Basic processing without options
  const result1Original = processOriginal(testData, {});
  const result1Refactored = processRefactored(testData, {});
  if (assertEqual(result1Refactored, result1Original, 'Test 1: Basic processing')) {
    passed++;
  } else {
    failed++;
  }

  // Test 2: Uppercase names
  const result2Original = processOriginal(testData, { uppercase: true });
  const result2Refactored = processRefactored(testData, { uppercase: true });
  if (assertEqual(result2Refactored, result2Original, 'Test 2: Uppercase names')) {
    passed++;
  } else {
    failed++;
  }

  // Test 3: Lowercase names
  const result3Original = processOriginal(testData, { lowercase: true });
  const result3Refactored = processRefactored(testData, { lowercase: true });
  if (assertEqual(result3Refactored, result3Original, 'Test 3: Lowercase names')) {
    passed++;
  } else {
    failed++;
  }

  // Test 4: Masked emails
  const result4Original = processOriginal(testData, { maskEmail: true });
  const result4Refactored = processRefactored(testData, { maskEmail: true });
  if (assertEqual(result4Refactored, result4Original, 'Test 4: Masked emails')) {
    passed++;
  } else {
    failed++;
  }

  // Test 5: Country codes
  const result5Original = processOriginal(testData, { countryCode: true });
  const result5Refactored = processRefactored(testData, { countryCode: true });
  if (assertEqual(result5Refactored, result5Original, 'Test 5: Country codes')) {
    passed++;
  } else {
    failed++;
  }

  // Test 6: Sort by name
  const result6Original = processOriginal(testData, { sortBy: 'name' });
  const result6Refactored = processRefactored(testData, { sortBy: 'name' });
  if (assertEqual(result6Refactored, result6Original, 'Test 6: Sort by name')) {
    passed++;
  } else {
    failed++;
  }

  // Test 7: Sort by age
  const result7Original = processOriginal(testData, { sortBy: 'age' });
  const result7Refactored = processRefactored(testData, { sortBy: 'age' });
  if (assertEqual(result7Refactored, result7Original, 'Test 7: Sort by age')) {
    passed++;
  } else {
    failed++;
  }

  // Test 8: Combined options
  const result8Original = processOriginal(testData, {
    uppercase: true,
    maskEmail: true,
    countryCode: true,
    sortBy: 'name',
  });
  const result8Refactored = processRefactored(testData, {
    uppercase: true,
    maskEmail: true,
    countryCode: true,
    sortBy: 'name',
  });
  if (assertEqual(result8Refactored, result8Original, 'Test 8: Combined options')) {
    passed++;
  } else {
    failed++;
  }

  // Test 9: Empty array
  const result9Original = processOriginal([], {});
  const result9Refactored = processRefactored([], {});
  if (assertEqual(result9Refactored, result9Original, 'Test 9: Empty array')) {
    passed++;
  } else {
    failed++;
  }

  // Test 10: Invalid data
  const invalidData = [null, undefined, {}, { name: '' }, { age: 30 }];
  const result10Original = processOriginal(invalidData, {});
  const result10Refactored = processRefactored(invalidData, {});
  if (assertEqual(result10Refactored, result10Original, 'Test 10: Invalid data')) {
    passed++;
  } else {
    failed++;
  }

  // Summary
  console.log(`\n${'='.repeat(50)}`);
  console.log(`Total tests: ${passed + failed}`);
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  console.log(`${'='.repeat(50)}`);

  if (failed === 0) {
    console.log('\n✓ All tests passed! Refactored code maintains same behavior.');
    process.exit(0);
  } else {
    console.error('\n✗ Some tests failed. Behavior has changed.');
    process.exit(1);
  }
}

runTests();
