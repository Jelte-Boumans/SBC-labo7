def adcencrypt(adcseed, adc):
  binadc = bin(adc)
  l = len(binadc)
  if l<18:
     for fill in range(18 - l):
       binadc = binadc[0:2] + "0" + binadc[2:]
  adcencrypted = ""
  for n in range(16):
     adcbit = binadc[17-n:18-n]
     seedletter = adcseed[n:n+1]
     seedbin = bin(ord(seedletter))
     if ( seedbin[5:6] == "0" ):
        seedbin = seedbin[0:5] + adcbit + seedbin[6:]
     elif ( seedbin[5:6] == "1" ):
       if adcbit == "1":
         adcbit ="0"
       elif adcbit == "0":
         adcbit ="1"
       seedbin = seedbin[0:5] + adcbit + seedbin[6:]
     encryptletter = chr(int(seedbin,2))
     adcencrypted = adcencrypted + encryptletter
  return adcencrypted

def adcdecrypt (adcseed, adcenc):
  adcbinnr="0b"
  for n in range(16):
    decletter = adcenc[15-n:16-n]
    decbin = bin(ord(decletter))
    decbit = decbin[5:6]
    seedletter = adcseed[15-n:16-n]
    seedbin = bin(ord(seedletter))
    seedbit = seedbin[5:6]
    if seedbit == "0":
       adcbinnr = adcbinnr + decbit
    elif seedbit == "1":
       if decbit == "0":
         decbit = "1"
       elif decbit == "1":
         decbit = "0"
       adcbinnr = adcbinnr + decbit
  adcdecimal= int(adcbinnr,2)
  return adcdecimal
