<?xml version="1.0" encoding="utf-8"?>
<FieldList>
  <Field ID="MTI">
    <FriendlyName>MTI</FriendlyName>
    <FieldType>N4</FieldType>
    <FieldBinary>31 31 30 30</FieldBinary>
    <FieldViewable>1100</FieldViewable>
    <ToolComment>[1100] Authorization request</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.002">
    <FriendlyName>Primary account number</FriendlyName>
    <SearchSymbol Name="PAN" Value="36070500001186"/>
    <FieldType>N..19</FieldType>
    <FieldBinary>33 36 30 37 30 35 30 30 30 30 31 31 38 36</FieldBinary>
    <FieldViewable>36070500001186</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.003">
    <FriendlyName>Processing code</FriendlyName>
    <SearchSymbol Name="PROCESSINGCODE" Value="000000"/>
    <FieldType>AN6</FieldType>
    <FieldBinary>30 30 30 30 30 30</FieldBinary>
    <FieldViewable>000000</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList>
      <Field ID="NET.1100.DE.003.SE.001">
        <FriendlyName>Processing code</FriendlyName>
        <FieldType>AN2</FieldType>
        <FieldBinary>30 30</FieldBinary>
        <FieldViewable>00</FieldViewable>
        <ToolComment>[00] Goods and services</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.003.SE.002">
        <FriendlyName>From account</FriendlyName>
        <FieldType>N2</FieldType>
        <FieldBinary>30 30</FieldBinary>
        <FieldViewable>00</FieldViewable>
        <ToolComment>[00] Default account</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.003.SE.003">
        <FriendlyName>To account</FriendlyName>
        <FieldType>N2</FieldType>
        <FieldBinary>30 30</FieldBinary>
        <FieldViewable>00</FieldViewable>
        <ToolComment>[00] Default account</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
    </FieldList>
  </Field>
  <Field ID="NET.1100.DE.004">
    <FriendlyName>Amount, transaction</FriendlyName>
    <FieldType>N12</FieldType>
    <FieldBinary>30 30 30 30 30 30 30 30 35 31 30 30</FieldBinary>
    <FieldViewable>000000005100</FieldViewable>
    <ToolComment>Value of 5100</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.007">
    <FriendlyName>Date + time, transmission</FriendlyName>
    <FieldType>N10</FieldType>
    <FieldBinary>31 30 31 38 30 39 30 35 34 31</FieldBinary>
    <FieldViewable>1018090541</FieldViewable>
    <ToolComment>Date and time of [2024-10-18 09:05:41]</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.011">
    <FriendlyName>System trace audit number</FriendlyName>
    <SearchSymbol Name="STAN" Value="503848"/>
    <FieldType>AN6</FieldType>
    <FieldBinary>35 30 33 38 34 38</FieldBinary>
    <FieldViewable>503848</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.012">
    <FriendlyName>Date + time, local transaction</FriendlyName>
    <FieldType>N12</FieldType>
    <FieldBinary>32 34 31 30 31 38 31 31 30 35 33 39</FieldBinary>
    <FieldViewable>241018110539</FieldViewable>
    <ToolComment>Date and time of [2024-10-18 11:05:39]</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.022">
    <FriendlyName>POS entry mode</FriendlyName>
    <FieldType>AN12</FieldType>
    <FieldBinary>39 31 30 31 30 31 35 30 31 38 30 31</FieldBinary>
    <FieldViewable>910101501801</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList>
      <Field ID="NET.1100.DE.022.SE.001">
        <FriendlyName>Card data input capability</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>39</FieldBinary>
        <FieldViewable>9</FieldViewable>
        <ToolComment>[9] Hybrid Terminal</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.002">
        <FriendlyName>Cardmember authentication capability</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>31</FieldBinary>
        <FieldViewable>1</FieldViewable>
        <ToolComment>[1] PIN</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.003">
        <FriendlyName>Card capture capability</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>30</FieldBinary>
        <FieldViewable>0</FieldViewable>
        <ToolComment>[0] None</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.004">
        <FriendlyName>Operating environment</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>31</FieldBinary>
        <FieldViewable>1</FieldViewable>
        <ToolComment>[1] On premises of card acceptor, attended</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.005">
        <FriendlyName>Cardmember present</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>30</FieldBinary>
        <FieldViewable>0</FieldViewable>
        <ToolComment>[0] Cardmember present</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.006">
        <FriendlyName>Card present</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>31</FieldBinary>
        <FieldViewable>1</FieldViewable>
        <ToolComment>[1] Card present</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.007">
        <FriendlyName>Card data input mode</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>35</FieldBinary>
        <FieldViewable>5</FieldViewable>
        <ToolComment>[5] ICC</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.008">
        <FriendlyName>Cardmember authentication</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>30</FieldBinary>
        <FieldViewable>0</FieldViewable>
        <ToolComment>[0] No authentication</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.009">
        <FriendlyName>Cardmember authentication entity</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>31</FieldBinary>
        <FieldViewable>1</FieldViewable>
        <ToolComment>[1] ICC</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.010">
        <FriendlyName>Card data output capability</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>38</FieldBinary>
        <FieldViewable>8</FieldViewable>
        <ToolComment>[8] Contactless</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.011">
        <FriendlyName>Terminal output capability</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>30</FieldBinary>
        <FieldViewable>0</FieldViewable>
        <ToolComment>[0] Unknown</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
      <Field ID="NET.1100.DE.022.SE.012">
        <FriendlyName>PIN capture capability</FriendlyName>
        <FieldType>AN1</FieldType>
        <FieldBinary>31</FieldBinary>
        <FieldViewable>1</FieldViewable>
        <ToolComment>[1] Device pin capture capability unknown</ToolComment>
        <ToolCommentLevel>INFO</ToolCommentLevel>
        <FieldList/>
      </Field>
    </FieldList>
  </Field>
  <Field ID="NET.1100.DE.023">
    <FriendlyName>Card sequence number</FriendlyName>
    <FieldType>N3</FieldType>
    <FieldBinary>30 30 31</FieldBinary>
    <FieldViewable>001</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.024">
    <FriendlyName>Function code</FriendlyName>
    <FieldType>N3</FieldType>
    <FieldBinary>31 30 30</FieldBinary>
    <FieldViewable>100</FieldViewable>
    <ToolComment>[100] Original authorization - amount accurate</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.026">
    <FriendlyName>Merchant category code</FriendlyName>
    <FieldType>N4</FieldType>
    <FieldBinary>37 30 31 31</FieldBinary>
    <FieldViewable>7011</FieldViewable>
    <ToolComment>[7011] - Lodging Hotels, Motels, And Resorts</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.032">
    <FriendlyName>Acquirer institution ID</FriendlyName>
    <FieldType>N..11</FieldType>
    <FieldBinary>30 30 30 30 30 33 36 37 36 33 31</FieldBinary>
    <FieldViewable>00000367631</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.033">
    <FriendlyName>Forwarding institution ID</FriendlyName>
    <FieldType>N..11</FieldType>
    <FieldBinary>30 30 30 30 30 33 36 31 39 30 30</FieldBinary>
    <FieldViewable>00000361900</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.035">
    <FriendlyName>Track 2 Data</FriendlyName>
    <FieldType>Z=D..40</FieldType>
    <FieldBinary>33 36 30 37 30 35 30 30 30 30 31 31 38 36 3D 32 33 31 32 32 30 31 31 32 30 31 30 30 30 32 36 33 30 30 30 30 30</FieldBinary>
    <FieldViewable>36070500001186=2312201120100026300000</FieldViewable>
    <ToolComment>PAN [36070500001186], Expiry [2023-12-31], Service code [201], Discretionary data [120100026300000]</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.037">
    <FriendlyName>Acquirer reference number</FriendlyName>
    <SearchSymbol Name="RRN" Value="429209503848"/>
    <FieldType>AN12</FieldType>
    <FieldBinary>34 32 39 32 30 39 35 30 33 38 34 38</FieldBinary>
    <FieldViewable>429209503848</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.041">
    <FriendlyName>Card acceptor terminal ID</FriendlyName>
    <SearchSymbol Name="TERMINALID" Value="U0119998"/>
    <FieldType>ANS8</FieldType>
    <FieldBinary>55 30 31 31 39 39 39 38</FieldBinary>
    <FieldViewable>U0119998</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.042">
    <FriendlyName>Card acceptor ID</FriendlyName>
    <SearchSymbol Name="MERCHANTID" Value="000104960038316"/>
    <FieldType>ANS15</FieldType>
    <FieldBinary>30 30 30 31 30 34 39 36 30 30 33 38 33 31 36</FieldBinary>
    <FieldViewable>000104960038316</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.043">
    <FriendlyName>Card acceptor name, location</FriendlyName>
    <FieldType>ANS..99</FieldType>
    <FieldBinary>54 72 75 73 74 20 54 65 73 74 69 6E 67 20 28 42 61 6E 67 6F 72 29 20 20 20 5C 5C 35 30 32 30 20 53 61 6C 7A 62 75 72 67 5C 20 20 20 20 20 20 20 20 20 20 20 20 20 30 34 30</FieldBinary>
    <FieldViewable>TrustTesting(Bangor)\\5020Salzburg\040</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.049">
    <FriendlyName>Currency code, transaction</FriendlyName>
    <FieldType>N3</FieldType>
    <FieldBinary>39 37 38</FieldBinary>
    <FieldViewable>978</FieldViewable>
    <ToolComment>Euro (978, EUR)</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.052">
    <FriendlyName>Primary PIN block</FriendlyName>
    <FieldType>B8</FieldType>
    <FieldBinary>0F 4F 19 8A F5 D6 EC B7</FieldBinary>
    <FieldViewable>0F4F198AF5D6ECB7</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055">
    <FriendlyName>ICC data</FriendlyName>
    <FieldType>B...256</FieldType>
    <FieldBinary>9F 02 06 00 00 00 00 51 00 82 02 58 00 9F 36 02 00 01 9F 26 08 5F B0 99 8A 39 FB 7F F4 9F 27 01 80 9F 34 03 41 03 02 84 07 A0 00 00 01 52 30 10 9F 1E 08 32 35 33 37 30 36 30 38 9F 10 08 01 05 90 1C 00 00 00 00 9F 09 02 00 01 9F 33 03 60 F0 C8 9F 1A 02 00 40 9F 35 01 22 95 05 42 40 00 80 00 9A 03 24 10 18 9C 01 00 5F 2A 02 09 78 9F 37 04 9C 8A 48 CF</FieldBinary>
    <FieldViewable>9F0206000000005100820258009F360200019F26085FB0998A39FB7FF49F2701809F34034103028407A00000015230109F1E0832353337303630389F10080105901C000000009F090200019F330360F0C89F1A0200409F350122950542400080009A032410189C01005F2A0209789F37049C8A48CF</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F02">
    <FriendlyName>Amount (Authorized) Numeric</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F02" Name="Amount (Authorized) Numeric" Format="TLV"/>
    <FieldBinary>9F 02 06 00 00 00 00 51 00</FieldBinary>
    <FieldViewable>000000005100</FieldViewable>
    <ToolComment>Value of 5100</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.82">
    <FriendlyName>Application Interchange Profile</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="82" Name="Application Interchange Profile" Format="TLV"/>
    <FieldBinary>82 02 58 00</FieldBinary>
    <FieldViewable>00</FieldViewable>
    <ToolComment>Default</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F36">
    <FriendlyName>Application Transaction Counter</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F36" Name="Application Transaction Counter" Format="TLV"/>
    <FieldBinary>9F 36 02 00 01</FieldBinary>
    <FieldViewable>0001</FieldViewable>
    <ToolComment>Value of 0x1 (1)</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F26">
    <FriendlyName>Authorization Request Cryptogram</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F26" Name="Authorization Request Cryptogram" Format="TLV"/>
    <FieldBinary>9F 26 08 5F B0 99 8A 39 FB 7F F4</FieldBinary>
    <FieldViewable>5FB0998A39FB7FF4</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F27">
    <FriendlyName>Cryptogram Information Data</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F27" Name="Cryptogram Information Data" Format="TLV"/>
    <FieldBinary>9F 27 01 80</FieldBinary>
    <FieldViewable>80</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F34">
    <FriendlyName>Cardholder Verification Method Results</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F34" Name="Cardholder Verification Method Results" Format="TLV"/>
    <FieldBinary>9F 34 03 41 03 02</FieldBinary>
    <FieldViewable>410302</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.84">
    <FriendlyName>Application Identifier (Card)</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="84" Name="Application Identifier (Card)" Format="TLV"/>
    <FieldBinary>84 07 A0 00 00 01 52 30 10</FieldBinary>
    <FieldViewable>000001523010</FieldViewable>
    <ToolComment>A0000001523010 - D-PAS</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F1E">
    <FriendlyName>Interface Device Serial Number</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F1E" Name="Interface Device Serial Number" Format="TLV"/>
    <FieldBinary>9F 1E 08 32 35 33 37 30 36 30 38</FieldBinary>
    <FieldViewable>3235333730363038</FieldViewable>
    <ToolComment>&quot;25370608&quot;</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F10">
    <FriendlyName>Issuer Application Data</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F10" Name="Issuer Application Data" Format="TLV"/>
    <FieldBinary>9F 10 08 01 05 90 1C 00 00 00 00</FieldBinary>
    <FieldViewable>0105901C00000000</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>KDI (Key Derivation Index): 0x01</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>CVN (Cryptogram Version Number): 0x05 - Assuming D-PAS</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>CVR (Card Verification Results): '901C00000000'</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>CVR.Byte 1 Bits 8-7: 10 - Second GENERATE AC not requested</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>CVR.Byte 1 Bits 6-5: 01 - TC returned in first GENERATE AC</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>CVR.Byte 2 Bit 5: 1 - Offline PIN Verification performed</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>CVR.Byte 2 Bit 4: 1 - Offline Enciphered PIN Verification performed</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="">
    <FriendlyName/>
    <FieldType/>
    <FieldBinary/>
    <FieldViewable/>
    <ToolComment>CVR.Byte 2 Bit 3: 1 - Offline PIN Verification Successful</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F09">
    <FriendlyName>Terminal Application Version Number</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F09" Name="Terminal Application Version Number" Format="TLV"/>
    <FieldBinary>9F 09 02 00 01</FieldBinary>
    <FieldViewable>0001</FieldViewable>
    <ToolComment>Value of 0x1 (1)</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F33">
    <FriendlyName>Terminal Capability Profile</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F33" Name="Terminal Capability Profile" Format="TLV"/>
    <FieldBinary>9F 33 03 60 F0 C8</FieldBinary>
    <FieldViewable>60F0C8</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F1A">
    <FriendlyName>Terminal Country Code</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F1A" Name="Terminal Country Code" Format="TLV"/>
    <FieldBinary>9F 1A 02 00 40</FieldBinary>
    <FieldViewable>0040</FieldViewable>
    <ToolComment>[0040] - Austria</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F35">
    <FriendlyName>EMV Terminal Type</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F35" Name="EMV Terminal Type" Format="TLV"/>
    <FieldBinary>9F 35 01 22</FieldBinary>
    <FieldViewable>22</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.95">
    <FriendlyName>Terminal Verification Results</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="95" Name="Terminal Verification Results" Format="TLV"/>
    <FieldBinary>95 05 42 40 00 80 00</FieldBinary>
    <FieldViewable>40008000</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9A">
    <FriendlyName>Transaction Date</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9A" Name="Transaction Date" Format="TLV"/>
    <FieldBinary>9A 03 24 10 18</FieldBinary>
    <FieldViewable>1018</FieldViewable>
    <ToolComment>[241018] - 2024-Oct-18</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9C">
    <FriendlyName>Transaction Type</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9C" Name="Transaction Type" Format="TLV"/>
    <FieldBinary>9C 01 00</FieldBinary>
    <FieldViewable/>
    <ToolComment>Value of 0x0 (0)</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.5F2A">
    <FriendlyName>Transaction Currency Code</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="5F2A" Name="Transaction Currency Code" Format="TLV"/>
    <FieldBinary>5F 2A 02 09 78</FieldBinary>
    <FieldViewable>0978</FieldViewable>
    <ToolComment>[0978] - Euro</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.055.TAG.9F37">
    <FriendlyName>Unpredictable Number</FriendlyName>
    <FieldType>TLV</FieldType>
    <EMVData Tag="9F37" Name="Unpredictable Number" Format="TLV"/>
    <FieldBinary>9F 37 04 9C 8A 48 CF</FieldBinary>
    <FieldViewable>9C8A48CF</FieldViewable>
    <ToolComment>[9C8A48CF]</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.092">
    <FriendlyName>Country code, transaction origin</FriendlyName>
    <FieldType>N3</FieldType>
    <FieldBinary>30 34 30</FieldBinary>
    <FieldViewable>040</FieldViewable>
    <ToolComment>Austria (040/AT/AUT)</ToolComment>
    <ToolCommentLevel>INFO</ToolCommentLevel>
    <FieldList/>
  </Field>
  <Field ID="NET.1100.DE.100">
    <FriendlyName>Receiving institution ID</FriendlyName>
    <FieldType>N..11</FieldType>
    <FieldBinary>30 30 30 30 30 33 36 31 35 38 39</FieldBinary>
    <FieldViewable>00000361589</FieldViewable>
    <ToolComment>Default</ToolComment>
    <FieldList/>
  </Field>
</FieldList>
