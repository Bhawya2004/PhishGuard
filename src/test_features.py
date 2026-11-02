from features import extract_features

samples = [
    "https://www.google.com/search?q=shoes",
    "http://192.168.1.5/secure-login/paypal-verify.php",
    "http://paypal.account-verify.xyz/signin?id=123@abc",
]
for s in samples:
    print(s)
    print(extract_features(s), "\n")