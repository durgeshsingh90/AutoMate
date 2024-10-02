// Load JSON definitions on page load
let fieldDefinitions = {};

window.onload = function() {
    fetch('/get-field-definitions/')
    .then(response => response.json())
    .then(data => {
        fieldDefinitions = data.fields; // Access the 'fields' object
        console.log('Field definitions loaded:', fieldDefinitions);
    })
    .catch(error => {
        console.error('Error loading field definitions:', error);
    });
};

function validateBitmaps() {
    const inputMessage = document.getElementById("inputMessage").value;
    const validationResult = document.getElementById("validationResult");

    // Parse the input message as JSON
    let inputObj;
    try {
        inputObj = JSON.parse(inputMessage);
    } catch (e) {
        validationResult.innerHTML = "<span class='error'>Invalid JSON format!</span>";
        return;
    }

    let errors = [];

    // Loop through the input bitmaps and validate against JSON definitions
    for (const fieldKey in inputObj) {
        if (fieldKey === "mti") {
            continue; // Skip MTI as it's not part of the fields definitions
        }

        let fieldNumber = fieldKey.replace("BM", "").padStart(3, '0'); // Normalize field number
        let fieldValue = inputObj[fieldKey];

        if (!fieldDefinitions[fieldNumber]) {
            errors.push(`Field ${fieldNumber} is not defined in the field definitions.`);
            continue;
        }

        let fieldDef = fieldDefinitions[fieldNumber];
        let expectedLength = fieldDef.length || fieldDef.max_length;

        if (fieldNumber === "055") {
            // Handle DE055 with subfields
            errors.push(...validateDE055(fieldValue, fieldDef.subfields));
        } else if (typeof fieldValue === "object") {
            // Handle composite fields like BM060
            errors.push(...validateCompositeField(fieldValue, fieldNumber, fieldDef));
        } else {
            // Validate field length
            if (expectedLength && fieldValue.toString().length > expectedLength) {
                errors.push(`Field ${fieldNumber} (${fieldDef.name}) exceeds the maximum length of ${expectedLength}.`);
            }
        }
    }

    // Show validation result
    if (errors.length > 0) {
        validationResult.innerHTML = "<span class='error'>" + errors.join('<br>') + "</span>";
    } else {
        validationResult.innerHTML = "<span>Validation passed!</span>";
    }
}

function validateDE055(fieldValue, subfields) {
    let errors = [];
    // Assuming fieldValue is a hex string representing TLV data
    // Implement TLV parsing logic here
    // For illustration purposes, let's assume fieldValue is an object
    let de055Fields;
    try {
        // Convert fieldValue from hex string to object if necessary
        de055Fields = parseTLV(fieldValue); // You need to implement parseTLV
    } catch (e) {
        errors.push("Invalid DE055 format.");
        return errors;
    }

    for (const tag in de055Fields) {
        if (!subfields[tag]) {
            errors.push(`Subfield ${tag} is not defined in DE055 subfields.`);
            continue;
        }
        let expectedLength = subfields[tag].max_length;
        let value = de055Fields[tag];

        if (value.length > expectedLength * 2) { // Multiply by 2 if value is in hex
            errors.push(`Subfield ${tag} (${subfields[tag].name}) exceeds maximum length of ${expectedLength}.`);
        }
    }

    return errors;
}

function validateCompositeField(fieldValue, fieldNumber, fieldDef) {
    let errors = [];
    // Implement validation logic for composite fields
    for (const subfield in fieldValue) {
        // You can define subfield validations here
        // For now, we can just check that the subfields exist
        if (!fieldDef.subfields || !fieldDef.subfields[subfield]) {
            errors.push(`Subfield ${subfield} in Field ${fieldNumber} is not defined.`);
        }
    }
    return errors;
}

function parseTLV(hexString) {
    // Implement TLV parsing logic here
    // This function should return an object with tag-value pairs
    // For example: { "9F1A": "1234", "5F2A": "5678" }
    let result = {};
    let index = 0;

    while (index < hexString.length) {
        // Read tag
        let tag = hexString.substr(index, 2);
        index += 2;

        // Check for multi-byte tag
        if ((parseInt(tag, 16) & 0x1F) === 0x1F) {
            tag += hexString.substr(index, 2);
            index += 2;
        }

        // Read length
        let lengthHex = hexString.substr(index, 2);
        index += 2;
        let length = parseInt(lengthHex, 16);

        // Read value
        let value = hexString.substr(index, length * 2);
        index += length * 2;

        result[tag] = value;
    }

    return result;
}
