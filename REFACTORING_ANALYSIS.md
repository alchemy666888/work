# Refactoring Analysis: processUserData Function

## Complexity Issues Identified

### 1. **Multiple Responsibilities**
The function handles:
- Data validation
- Name formatting
- Age parsing and categorization
- Email masking
- Address processing
- Country code conversion
- Sorting

### 2. **Deep Nesting**
- Up to 5-6 levels of nested conditionals
- Makes code hard to read and follow
- Increases cognitive load

### 3. **Code Duplication**
- Repeated option checks (`options && options.X`)
- Similar validation patterns

### 4. **Hard-coded Logic**
- Country code mappings embedded in the main function
- Age category thresholds hard-coded

### 5. **Poor Testability**
- Cannot test individual processing steps in isolation
- Difficult to add new transformations

## Refactoring Strategy

### 1. **Extract Helper Functions**
- Create small, focused functions for each responsibility
- Each function should do one thing well

### 2. **Reduce Nesting**
- Use early returns and guard clauses
- Extract nested logic into separate functions

### 3. **Separate Configuration from Logic**
- Move hard-coded values to constants
- Make country mapping a separate function

### 4. **Improve Naming**
- Use descriptive function and variable names
- Make intent clear

### 5. **Maintain Behavior**
- Ensure all edge cases are handled
- Same input produces same output
