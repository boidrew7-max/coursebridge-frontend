const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  // Configuration
  const DEBUG = process.env.DEBUG === 'true';
  const rawDir = path.resolve(__dirname, '../data/raw/assist/debug_ccsf_ucberkeley_clean');
  const outDir = path.resolve(__dirname, '../data/processed');

  // Create directories
  if (!fs.existsSync(rawDir)) fs.mkdirSync(rawDir, { recursive: true });
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  // Launch browser
  const browser = await chromium.launch({ headless: !DEBUG }); // Show browser when debugging
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('Navigating to ASSIST...');
  await page.goto('https://www.assist.org', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Save initial state if debugging
  if (DEBUG) {
    await page.screenshot({ path: path.join(rawDir, '00_initial.png') });
    fs.writeFileSync(path.join(rawDir, '00_initial.html'), await page.content());
  }

  // Skip API fetching - use UI interactions only
  console.log('Skipping API fetch - will select institutions via UI...');

  // Step 2: Set Institution to CCSF
  console.log('Setting Institution to CCSF...');
  const institutionLabel = page.getByLabel(/Institution/i).first();
  await institutionLabel.waitFor({ state: 'attached', timeout: 15000 });
  await institutionLabel.click();
  await page.waitForTimeout(500);

  // Wait for options to appear
  await page.waitForFunction(() => document.querySelectorAll('[role="option"]').length > 0, { timeout: 5000 });
  const institutionOptions = await page.$$('[role="option"]');
  let institutionSelected = false;
  for (const opt of institutionOptions) {
    const txt = await opt.textContent();
    if (txt.includes('City College of San Francisco') || txt.includes('CCSF')) {
      await opt.click();
      institutionSelected = true;
      console.log(`Selected Institution via option: ${txt}`);
      break;
    }
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);

  if (!institutionSelected) {
    console.warn('Could not select CCSF from options; trying to set value via input...');
    const institutionInput = await page.evaluate((labelElement) => {
      const labelId = labelElement.id;
      if (labelId) {
        const inputByAriaLabelledBy = document.querySelector(`input[aria-labelledby="${labelId}"], select[aria-labelledby="${labelId}"]`);
        if (inputByAriaLabelledBy) return inputByAriaLabelledBy;
      }
      if (labelElement.matches('input, select')) return labelElement;
      const inputInside = labelElement.querySelector('input, select');
      if (inputInside) return inputInside;
      let prev = labelElement.previousElementSibling;
      while (prev) {
        if (prev.matches('input, select')) return prev;
        prev = prev.previousElementSibling;
      }
      let next = labelElement.nextElementSibling;
      while (next) {
        if (next.matches('input, select')) return next;
        next = next.nextElementSibling;
      }
      let parent = labelElement.parentElement;
      while (parent && parent !== document.body) {
        const input = parent.querySelector('input, select');
        if (input) return input;
        parent = parent.parentElement;
      }
      return null;
    }, institutionLabel);

    if (institutionInput) {
      await institutionInput.fill('CCSF'); // We know the code is CCSF
      await institutionInput.dispatchEvent(new Event('change', { bubbles: true }));
      console.log(`Set Institution value directly to: CCSF`);
    } else {
      console.error('Could not find Institution input to set value');
      await browser.close();
      return;
    }
  }
  await page.waitForTimeout(1000);

  // Academic Year is already set to latest by default - skip
  console.log('Academic Year is already set to latest by default - skipping...');
  await page.waitForTimeout(1000);

  // Step 4: Set Target Institution to UC Berkeley
  console.log('Setting Target Institution to UC Berkeley...');
  // We need to click the label for the second institution (target institution)
  // Find all labels with "Institution" text
  const institutionLabels = await page.$$('label:has-text("Institution")');
  console.log(`Found ${institutionLabels.length} labels with "Institution"`);

  if (institutionLabels.length < 2) {
    console.error('Expected at least 2 Institution labels (source and target), found:', institutionLabels.length);
    await browser.close();
    return;
  }

  // Try the second Institution label (index 1) as the target institution
  const targetInstitutionLabel = institutionLabels[1]; // Second Institution label
  const labelText = await targetInstitutionLabel.textContent();
  console.log(`Clicking target institution label (second Institution): "${labelText.trim()}"`);
  await targetInstitutionLabel.click();
  await page.waitForTimeout(500);

  await page.waitForFunction(() => document.querySelectorAll('[role="option"]').length > 0, { timeout: 5000 });
  const targetOptions = await page.$$('[role="option"]');
  let targetSelected = false;
  for (const opt of targetOptions) {
    const txt = await opt.textContent();
    if (txt.includes('University of California, Berkeley') || txt.includes('UC Berkeley')) {
      await opt.click();
      targetSelected = true;
      console.log(`Selected Target Institution via option: ${txt}`);
      break;
    }
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);

  if (!targetSelected) {
    console.warn('Could not select UC Berkeley from options; trying to set value via input...');
    const targetInput = await page.evaluate((labelElement) => {
      const labelId = labelElement.id;
      if (labelId) {
        const inputByAriaLabelledBy = document.querySelector(`input[aria-labelledby="${labelId}"], select[aria-labelledby="${labelId}"]`);
        if (inputByAriaLabelledBy) return inputByAriaLabelledBy;
      }
      if (labelElement.matches('input, select')) return labelElement;
      const inputInside = labelElement.querySelector('input, select');
      if (inputInside) return inputInside;
      let prev = labelElement.previousElementSibling;
      while (prev) {
        if (prev.matches('input, select')) return prev;
        prev = prev.previousElementSibling;
      }
      let next = labelElement.nextElementSibling;
      while (next) {
        if (next.matches('input, select')) return next;
        next = next.nextElementSibling;
      }
      let parent = labelElement.parentElement;
      while (parent && parent !== document.body) {
        const input = parent.querySelector('input, select');
        if (input) return input;
        parent = parent.parentElement;
      }
      return null;
    }, targetInstitutionLabel);

    if (targetInput) {
      // Try to set the value directly - we'll try common variations
      const possibleValues = [
        'University of California, Berkeley',
        'UC Berkeley',
        'University of California Berkeley',
        'UCB'
      ];

      let valueSet = false;
      for (const value of possibleValues) {
        try {
          await targetInput.fill(value);
          await targetInput.dispatchEvent(new Event('change', { bubbles: true }));
          console.log(`Set Target Institution value directly to: ${value}`);
          valueSet = true;
          break;
        } catch (e) {
          // Try next value
          continue;
        }
      }

      if (!valueSet) {
        console.error('Could not set Target Institution input value');
        await browser.close();
        return;
      }
    } else {
      console.error('Could not find Target Institution input to set value');
      await browser.close();
      return;
    }
  }
  await page.waitForTimeout(1000);

  // Step 4.5: Get selected Academic Year
  console.log('Getting selected Academic Year...');
  const yearLabel = page.getByLabel(/Academic Year/i).first();
  await yearLabel.waitFor({ state: 'attached', timeout: 5000 });

  // Helper function to get input associated with a label
  const getInputFromLabel = async (labelElement) => {
    // Get the label's id or for attribute
    const labelId = await labelElement.getAttribute('id');
    const labelFor = await labelElement.getAttribute('for');

    // Try to find input by aria-labelledby first (if label has id)
    if (labelId) {
      const inputByAriaLabelledBy = await page.$(`input[aria-labelledby="${labelId}"], select[aria-labelledby="${labelId}"]`);
      if (inputByAriaLabelledBy) return inputByAriaLabelledBy;
    }

    // Try to find input by for attribute
    if (labelFor) {
      const inputByFor = await page.$(`#${labelFor}`);
      if (inputByFor) return inputByFor;
    }

    // Check if the label itself is an input
    const isInput = await labelElement.evaluate(el => el.matches('input, select'));
    if (isInput) return labelElement;

    // Look for input inside the label
    const inputInside = await labelElement.$('input, select');
    if (inputInside) return inputInside;

    // Look for input before the label
    let prevEl = await labelElement.evaluateHandle(el => el.previousElementSibling);
    while (prevEl) {
      const prevElement = await prevEl.asElement();
      if (prevElement && await prevElement.evaluate(el => el.matches('input, select'))) {
        return prevElement;
      }
      prevEl = await prevEl.evaluateHandle(el => el.previousElementSibling);
    }

    // Look for input after the label
    let nextEl = await labelElement.evaluateHandle(el => el.nextElementSibling);
    while (nextEl) {
      const nextElement = await nextEl.asElement();
      if (nextElement && await nextElement.evaluate(el => el.matches('input, select'))) {
        return nextElement;
      }
      nextEl = await nextEl.evaluateHandle(el => el.nextElementSibling);
    }

    // Look for input in parent element
    let parentEl = await labelElement.evaluateHandle(el => el.parentElement);
    while (parentEl) {
      const parentElement = await parentEl.asElement();
      if (parentElement && !(await parentElement.evaluate(el => el === document.body))) {
        const input = await parentElement.$('input, select');
        if (input) return input;
      }
      parentEl = await parentEl.evaluateHandle(el => el.parentElement);
    }

    return null;
  };

  let selectedYear = '';
  const yearInput = await getInputFromLabel(yearLabel);
  if (yearInput) {
    selectedYear = await yearInput.inputValue();
    console.log(`Selected Academic Year via input value: ${selectedYear}`);
  } else {
    // Fallback: try to get the selected option from the combobox
    const labelId = await yearLabel.getAttribute('id');
    if (labelId) {
      const yearCombobox = await page.$(`[role="combobox"][aria-labelledby="${labelId}"]`);
      if (yearCombobox) {
        // Try to get the selected option's text
        const selectedOption = await yearCombobox.$('option[selected]');
        if (selectedOption) {
          selectedYear = await selectedOption.textContent();
          console.log(`Selected Academic Year via selected option: ${selectedYear}`);
        } else {
          // Fallback to the combobox's value
          selectedYear = await yearCombobox.inputValue();
          console.log(`Selected Academic Year via combobox value: ${selectedYear}`);
        }
      }
    }
  }

  if (!selectedYear) {
    console.warn('Could not determine Academic Year from UI; using empty string');
    selectedYear = '';
  }

  // Step 5: Leave Area of Study as default (to get all agreements)
  console.log('Leaving Area of Study as default to get all agreements...');

  // Step 6: Click View Agreements button
  console.log('Looking for View Agreements button...');
  const viewAgreementsBtn = page.getByRole('button', { name: /View Agreements/i }).first();
  const btnCount = await viewAgreementsBtn.count();
  if (btnCount === 0) {
    console.error('View Agreements button not found');
    if (DEBUG) {
      await page.screenshot({ path: path.join(rawDir, 'error_no_button.png') });
      fs.writeFileSync(path.join(rawDir, 'error_no_button.html'), await page.content());
    }
    await browser.close();
    return;
  }
  console.log('View Agreements button found');

  // Check if button is enabled
  await page.waitForTimeout(2000);
  let isDisabled = await viewAgreementsBtn.isDisabled();
  console.log(`View Agreements button disabled: ${isDisabled}`);

  // Try clicking anyway - sometimes it becomes enabled after selection
  console.log('Clicking View Agreements button...');
  await viewAgreementsBtn.click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  // Save state after click if debugging
  if (DEBUG) {
    fs.writeFileSync(path.join(rawDir, '01_after_click.html'), await page.content());
    await page.screenshot({ path: path.join(rawDir, '01_after_click.png') });
  }

  // Step 6.5: Select "All Majors" to load all agreements
  console.log('Selecting \"All Majors\" to load all agreements...');
  try {
    // Wait for the major list to appear (we expect to see text \"All Majors\")
    const allMajorsOption = page.getByText('All Majors', { exact: true }).first();
    await allMajorsOption.waitFor({ state: 'attached', timeout: 10000 });
    await allMajorsOption.click();
    console.log('Clicked \"All Majors\"');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Wait for articulations to load
  } catch (err) {
    console.warn('Could not click \"All Majors\" option:', err.message);
    // Continue anyway; maybe articulations are already loaded
  }

  // Save state after major selection if debugging
  if (DEBUG) {
    fs.writeFileSync(path.join(rawDir, '02_after_major_select.html'), await page.content());
    await page.screenshot({ path: path.join(rawDir, '02_after_major_select.png') });
  }

  // Step 7: Extract the articulation data
  console.log('Extracting articulation data...');

  // Let's first try to extract the year from the page title or header
  let pageYear = selectedYear;
  if (!pageYear || pageYear === '') {
    try {
      const title = await page.title();
      // Extract year from title like "2025-2026 All Majors Agreement"
      const yearMatch = title.match(/(\d{4})-(\d{2,4})/);
      if (yearMatch) {
        pageYear = yearMatch[1]; // Just take the first year (e.g., 2025)
        console.log(`Extracted year from title: ${pageYear}`);
      }
    } catch (e) {
      console.warn('Could not extract year from title:', e.message);
    }
  }

  // Try multiple selectors for articulation data
  const tables = await page.$$('table');
  console.log(`Found ${tables.length} tables after click`);

  // Also look for common articulation result patterns
  const resultItems = await page.$$('[class*="result"], [class*="agreement"], [class*="articulation"]');
  console.log(`Found ${resultItems.length} elements with result/agreement/articulation in class`);

  // Look for lists or divs that might contain course mappings
  const lists = await page.$$('ul, ol, dl');
  console.log(`Found ${lists.length} lists`);

  const divs = await page.$$('div');
  console.log(`Found ${divs.length} divs`);

  let agreements = [];

  // Process tables first
  for (let i = 0; i < tables.length; i++) {
    const table = tables[i];
    const headerRows = await table.$$('thead tr');
    let headerTexts = [];
    if (headerRows.length > 0) {
      for (const hr of headerRows) {
        const cells = await hr.$$('th');
        const texts = [];
        for (const c of cells) {
          texts.push(await c.textContent());
        }
        headerTexts.push(texts.join(' | '));
      }
    } else {
      const firstRow = await table.$$('tbody tr');
      if (firstRow.length > 0) {
        const cells = await firstRow[0].$$('td');
        const texts = [];
        for (const c of cells) {
          texts.push(await c.textContent());
        }
        headerTexts.push(texts.join(' | '));
      }
    }
    const headerJoined = headerTexts.join(' ; ');
    console.log(`Table ${i} headers: ${headerJoined}`);

    const lowerHeader = headerJoined.toLowerCase();
    if (lowerHeader.includes('course') && (lowerHeader.includes('ccsf') || lowerHeader.includes('community college') || lowerHeader.includes('uc') || lowerHeader.includes('university'))) {
      console.log(`  => This looks like an articulation table`);
      const rows = await table.$$('tbody tr');
      let startIdx = 0;
      if (headerRows.length === 0 && firstRow.length > 0) {
        startIdx = 1;
      }
      for (let r = startIdx; r < rows.length; r++) {
        const row = rows[r];
        const cells = await row.$$('td');
        const cellTexts = [];
        for (const c of cells) {
          cellTexts.push(await c.textContent());
        }
        agreements.push({
          tableIndex: i,
          header: headerJoined,
          cells: cellTexts
        });
      }
    }
  }

  // Extract articulations from text format
  if (agreements.length === 0) {
    console.log('No articulation tables found; trying to extract from page text...');
    const bodyText = await page.evaluate(() => document.body.innerText);
    if (DEBUG) {
      fs.writeFileSync(path.join(rawDir, 'page_text_after_click.txt'), bodyText);
    }

    const lines = bodyText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    let currentMajor = '';

    // Look for articulation patterns in the text
    for (const line of lines) {
      if (/Major:/i.test(line) || /Area of Study:/i.test(line)) {
        currentMajor = line.replace(/.*:/, '').trim();
        continue;
      }

      // Look for articulation patterns in the text format we observed:
      // UCB course (e.g., MATH 51)
      // title line
      // units number
      // "units"
      // CCSF course (e.g., MATH 110A)
      // title line
      // units number
      // "units"
      if (line.match(/^[A-Z]{2,}\s+\d{1,3}[A-Z]?$/)) {
        // This looks like a course code (either UCB or CCSF)
        const potentialUcbCourse = line;
        const lineIndex = lines.indexOf(line);

        // Check if we have enough lines ahead for the pattern:
        // [UCB course], title, units, "units", [CCSF course], title, units, "units"
        if (lineIndex + 7 < lines.length) {
          const title1 = lines[lineIndex + 1].trim();
          const units1 = lines[lineIndex + 2].trim();
          const unitsLabel = lines[lineIndex + 3].trim();
          const potentialCcsfCourse = lines[lineIndex + 4].trim();
          const title2 = lines[lineIndex + 5].trim();
          const units2 = lines[lineIndex + 6].trim();
          const unitsLabel2 = lines[lineIndex + 7].trim();

          // Validate the pattern:
          // 1. Line 0: looks like a course code (we already checked)
          // 2. Line 3: should be "units" (case insensitive)
          // 3. Line 4: should look like a course code (the CCSF course)
          // 4. Line 7: should be "units" (case insensitive)
          if (unitsLabel.toLowerCase() === 'units' &&
              unitsLabel2.toLowerCase() === 'units' &&
              potentialCcsfCourse.match(/^[A-Z]{2,}\s+\d{1,3}[A-Z]?$/)) {

            // We found a UCB -> CCSF articulation
            agreements.push({
              tableIndex: -1,
              header: 'Extracted from text pattern',
              cells: [potentialUcbCourse, potentialCcsfCourse, `${units1} units`]
            });

            // Skip ahead to avoid overlapping matches
            // We'll continue the loop normally; the index will increment
            // But we could skip the next 7 lines if we want to be aggressive
            // For now, let's just continue and let the loop increment normally
            // We'll rely on the fact that we're moving through the array
          }
        }
      }
    }
  }

  console.log(`Extracted ${agreements.length} potential agreement entries`);

  // Step 8: Build CSV
  const csvHeader = ['source_college','target_university','major','academic_year','required_uc_course_or_area','articulated_ccsf_course','notes','raw_agreement_url_or_id'];
  const csvRows = [];

  // Try to detect major from the page
  let majorDetected = '';
  try {
    const title = await page.title();
    if (title.includes('Major') || title.includes('Area')) {
      majorDetected = title;
    }
    const majorEls = await page.$$('text=/Major:/i');
    if (majorEls.length > 0) {
      const text = await majorEls[0].textContent();
      majorDetected = text.split(':')[1]?.trim() || majorDetected;
    }
    const areaEls = await page.$$('text=/Area of Study:/i');
    if (areaEls.length > 0) {
      const text = await areaEls[0].textContent();
      majorDetected = text.split(':')[1]?.trim() || majorDetected;
    }
  } catch (e) {
    // ignore
  }
  if (!majorDetected) majorDetected = 'All Majors';

  for (const agr of agreements) {
    const cells = agr.cells;
    let ccsfCourse = '';
    let ucCourse = '';
    let notes = '';
    if (cells.length >= 2) {
      ccsfCourse = cells[0].trim();
      ucCourse = cells[1].trim();
      if (cells.length > 2) {
        notes = cells.slice(2).join(' | ');
      }
    } else if (cells.length === 1) {
      const line = cells[0];
      const parts = line.split(/->|→/);
      if (parts.length === 2) {
        ccsfCourse = parts[0].trim();
        ucCourse = parts[1].trim();
      } else {
        notes = line;
      }
    } else {
      notes = cells.join(' | ');
    }
    csvRows.push([
      'CCSF',
      'UC Berkeley',
      majorDetected,
      selectedYear,
      ucCourse,
      ccsfCourse,
      notes,
      ''
    ]);
  }

  // If we got no agreements, write a placeholder
  if (csvRows.length === 0) {
    csvRows.push([
      'CCSF',
      'UC Berkeley',
      majorDetected,
      selectedYear,
      '',
      '',
      'No agreements extracted; see raw debug files',
      ''
    ]);
  }

  // Step 9: Write CSV
  const csv = [csvHeader, ...csvRows].map(r => r.map(v => `"${v.replace(/"/g, '""')}"`).join(',')).join('\n');
  fs.writeFileSync(path.join(outDir, 'assist_articulations.csv'), csv);
  console.log(`CSV written to ${path.join(outDir, 'assist_articulations.csv')} with ${csvRows.length} rows`);

  // Step 10: Save debug info
  if (DEBUG) {
    const debugInfo = {
      metadata: {
        timestamp: new Date().toISOString(),
        institution: 'CCSF',
        target: 'UC Berkeley',
        academicYear: selectedYear,
        majorDetected,
        pageTitle: await page.title(),
        url: page.url()
      },
      agreementsExtracted: agreements.length,
      rawAgreements: agreements
    };
    fs.writeFileSync(path.join(rawDir, 'debug.json'), JSON.stringify(debugInfo, null, 2));
    console.log(`Debug info saved to ${path.join(rawDir, 'debug.json')}`);
  }

  await browser.close();
  console.log('Done.');
})();