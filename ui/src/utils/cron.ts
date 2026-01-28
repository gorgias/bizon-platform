interface ValidationResult {
  valid: boolean
  error?: string
}

/**
 * Validates a cron expression.
 * Standard cron format: minute hour day month weekday
 */
export function validateCron(expression: string): ValidationResult {
  const trimmed = expression.trim()

  // Empty is valid (no schedule)
  if (!trimmed) {
    return { valid: true }
  }

  const parts = trimmed.split(/\s+/)
  if (parts.length !== 5) {
    return {
      valid: false,
      error: 'Cron must have 5 fields: minute hour day month weekday',
    }
  }

  const [minute, hour, day, month, weekday] = parts

  const ranges: Array<{
    name: string
    value: string
    min: number
    max: number
  }> = [
    { name: 'minute', value: minute, min: 0, max: 59 },
    { name: 'hour', value: hour, min: 0, max: 23 },
    { name: 'day', value: day, min: 1, max: 31 },
    { name: 'month', value: month, min: 1, max: 12 },
    { name: 'weekday', value: weekday, min: 0, max: 6 },
  ]

  for (const { name, value, min, max } of ranges) {
    const validation = validateCronField(value, min, max)
    if (!validation.valid) {
      return {
        valid: false,
        error: `Invalid ${name}: ${validation.error}`,
      }
    }
  }

  return { valid: true }
}

function validateCronField(
  value: string,
  min: number,
  max: number
): ValidationResult {
  // Handle wildcard
  if (value === '*') {
    return { valid: true }
  }

  // Handle step values (*/2, 0-59/5, etc.)
  const stepMatch = value.match(/^(.+)\/(\d+)$/)
  if (stepMatch) {
    const [, base, step] = stepMatch
    const stepNum = parseInt(step, 10)
    if (stepNum <= 0) {
      return { valid: false, error: `step value must be positive` }
    }
    // Validate the base part recursively (but without allowing another step)
    if (base !== '*') {
      const baseValidation = validateCronRange(base, min, max)
      if (!baseValidation.valid) {
        return baseValidation
      }
    }
    return { valid: true }
  }

  // Handle lists (1,2,3)
  if (value.includes(',')) {
    const items = value.split(',')
    for (const item of items) {
      const itemValidation = validateCronRange(item, min, max)
      if (!itemValidation.valid) {
        return itemValidation
      }
    }
    return { valid: true }
  }

  // Handle single value or range
  return validateCronRange(value, min, max)
}

function validateCronRange(
  value: string,
  min: number,
  max: number
): ValidationResult {
  // Handle range (1-5)
  if (value.includes('-')) {
    const [start, end] = value.split('-')
    const startNum = parseInt(start, 10)
    const endNum = parseInt(end, 10)

    if (isNaN(startNum) || isNaN(endNum)) {
      return { valid: false, error: `'${value}' is not a valid range` }
    }

    if (startNum < min || startNum > max) {
      return {
        valid: false,
        error: `${startNum} out of range (${min}-${max})`,
      }
    }

    if (endNum < min || endNum > max) {
      return {
        valid: false,
        error: `${endNum} out of range (${min}-${max})`,
      }
    }

    if (startNum > endNum) {
      return {
        valid: false,
        error: `range start ${startNum} greater than end ${endNum}`,
      }
    }

    return { valid: true }
  }

  // Handle single number
  const num = parseInt(value, 10)
  if (isNaN(num)) {
    return { valid: false, error: `'${value}' is not a valid number` }
  }

  if (num < min || num > max) {
    return {
      valid: false,
      error: `${num} out of range (${min}-${max})`,
    }
  }

  return { valid: true }
}

/**
 * Describes a cron expression in human-readable format.
 */
export function describeCron(expression: string): string | null {
  const trimmed = expression.trim()
  if (!trimmed) return null

  const parts = trimmed.split(/\s+/)
  if (parts.length !== 5) return null

  const [minute, hour, day, month, weekday] = parts

  // Handle some common patterns
  if (minute === '0' && hour === '*' && day === '*' && month === '*' && weekday === '*') {
    return 'Every hour at minute 0'
  }

  if (minute === '0' && hour === '0' && day === '*' && month === '*' && weekday === '*') {
    return 'Every day at midnight'
  }

  if (minute !== '*' && hour !== '*' && day === '*' && month === '*' && weekday === '*') {
    return `Every day at ${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
  }

  return null
}
