import hmac
import hashlib
from collections import defaultdict
import secrets
import string

def byteGenerator(serverSeed, clientSeed, nonce):
    currentRound = 0
    serverSeed = serverSeed.encode() if isinstance(serverSeed, str) else serverSeed
    while True:
        hmacObj = hmac.new(serverSeed, f"{clientSeed}:{nonce}:{currentRound}".encode(), hashlib.sha256)
        buffer = hmacObj.digest()
        for byte in buffer:
            yield byte
        currentRound += 1

def generate_random_seed(length):
    choicesH = "abcdef0123456789"
    seed = ''.join(secrets.choice(choicesH) for _ in range(length))
    return seed

def generateFloats(serverSeed, clientSeed, nonce, count):
    rng = byteGenerator(serverSeed, clientSeed, nonce)
    bytesList = []
    for _ in range(count * 4):
        bytesList.extend(next(rng) for _ in range(4))
    floats = []
    for i in range(0, len(bytesList), 4):
        byteChunk = bytesList[i:i+4]
        value = sum(byte * 256**(3-j) for j, byte in enumerate(byteChunk))
        floats.append(value / 2**32)
    return floats

def calculateLimbo(floatValue, houseEdge=.99):
    floatPoint = 1e8 / ((floatValue * 1e8) / houseEdge)
    crashPoint = int(floatPoint * 100) / 100
    return max(crashPoint, 1)

def analyzeResults(serverSeed, clientSeed, nonceRange, multiTarget):
    results = []
    currentStreak = 0
    targetHit = 0
    targetMiss = 0
    maxmissStreak = 0
    currentmissStreak = 0
    firstStreaks = defaultdict(int)
    targetWindow = 500
    twStart = 0
    twMean = 0

    for nonce in range(nonceRange):
        floats = generateFloats(serverSeed, clientSeed, nonce, 1)
        result = calculateLimbo(floats[0])
        results.append(result)
        
        if result >= multiTarget:
            currentStreak += 1
            targetHit += 1
            currentmissStreak = 0
            if currentStreak in range(3, 11) and firstStreaks[currentStreak] == 0:
                firstStreaks[currentStreak] = nonce - currentStreak + 1
        else:
            currentStreak = 0
            currentmissStreak += 1
            targetMiss += 1
            maxmissStreak = max(maxmissStreak, currentmissStreak)

    for i in range(0, len(results) - targetWindow):
        window = results[i:i + targetWindow]
        hits = sum(1 for x in window if x >= multiTarget)
        windowAverage = hits / targetWindow
        if windowAverage > twMean:
            twMean = windowAverage
            twStart = i


            
    return {
        'averageTotal': 1 / (nonceL / targetHit),
        'first_streaks': dict(firstStreaks),
        'max_miss_streak': maxmissStreak,
        'best_window': {
            'start': twStart,
            'end': twStart + targetWindow,
            'average': twMean
            
        }
    }

# Example usage
print("If you want to change the length of the analysis every time, un-comment out the other line with the variable nonceL, and delete the other line.")
print("You can also adjust the target window width in the code.")
print("Note that larger windows will require more compute time for a weaker computer.")
serverSeed = input("Please input the server seed, or type 'random' or blank to generate a random seed: ").strip()
if serverSeed == "random" or serverSeed == "":
    serverSeed = generate_random_seed(64)

clientSeed = input("Please input the client seed, or type 'random' or blank to generate a random seed: ").strip()
if clientSeed == "random" or clientSeed == "":
    clientSeed = generate_random_seed(64)

## nonceL = int(input("Enter range to analyze as an integer...": )) 
nonceL = 20000


targetMulti = int(input("Input the target multi as an integer or decimal... (i.e.: 4.2, 4.0, 8.47): "))

analysis = analyzeResults(serverSeed, clientSeed, nonceL, targetMulti)

print("")
print("~Analysis~")
print(f"Length of Analysis: {nonceL} nonces.")
print("")
print(f"Server Seed: {serverSeed}")
print(f"Client Seed: {clientSeed}")
print("")
print("")
print(f"Expected Hitrate: {(1 / targetMulti) * 0.99}%")
print(f"Actual Hitrate: {analysis['averageTotal']}%")
print(f"First streaks: {analysis['first_streaks']}")
print(f"Max miss streak: {analysis['max_miss_streak']}")
print(f"Best window: Nonces {analysis['best_window']['start']}-{analysis['best_window']['end']} (Avg: {analysis['best_window']['average']:.4f})")
