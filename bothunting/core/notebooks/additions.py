def get_all_tweets(screen_name):
    """:returns: list of tweets which are stored as a list ([tweet id, tweet creation date, tweet text]) in the list
    and also writes the data into a csv file"""
    # initialize a list to hold all the tweepy Tweets
    alltweets = []
    # make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    # save most recent tweets
    alltweets.extend(new_tweets)
    # save the id of the oldest tweet less one
    if len(alltweets) > 0:
        oldest = alltweets[-1].id - 1
    # keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        print(f"getting tweets before {oldest}")
        # all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name=screen_name, count=200, max_id=oldest)  # , tweet_mode='extended'
        # save most recent tweets
        alltweets.extend(new_tweets)
        # update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
        print(f"...{len(alltweets)} tweets downloaded so far")
    # transform the tweepy tweets into a 2D array that will populate the csv
    outtweets = [[tweet.id_str, tweet.created_at, tweet.text] for tweet in alltweets]   # tweet.full_text
    # write the csv
    with open(f'new_{screen_name}_tweets.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "created_at", "text"])
        writer.writerows(outtweets)
    return outtweets
    pass


def get_links(tweet_text):
    tweet_text = tweet_text.replace("https://pbs.twimg.com/", "")
    return [t for t in tweet_text.split(" ") if "http" in t], tweet_text.count("http")


def get_account_data(screen_name):
    """:returns: None if the account does not exist or else the account data"""
    try:
        user_data = api.get_user(screen_name)
        return user_data
    except:
        return None


def get_account_creation_date(screen_name):
    """:returns: None if the account does not exist or else account's creation date"""
    c = get_account_data(screen_name)
    if c is not None:
        return c.created_at
    return None


def get_time_of_existance(screen_name):
    """:returns: None if the account does not exist or else the amount of days since the account's creation"""
    c = get_account_creation_date(screen_name)
    if c is not None:
        return (datetime.datetime.now() - c).days
    return None


def get_tweets_over_time(screen_name):
    """:returns: dictionary with all days as dates since the account's creation as keys and the amount of tweets tweeted
    on that day as values"""
    counter = {}
    creation_date = get_account_creation_date(screen_name)
    creation_date = datetime.date(year=creation_date.year, month=creation_date.month, day=creation_date.day)
    today = datetime.date.today()
    for i in range(0, (today - creation_date).days + 1):
        counter[creation_date + datetime.timedelta(days=i)] = 0
    for tweet in get_all_tweets(screen_name):
        date = tweet[1]
        counter[datetime.date(year=date.year, month=date.month, day=date.day)] += 1
    return counter


def get_inactive_days(screen_name):
    """:returns: number of days since the account's creation on which was not tweeted"""
    return len([d for d in get_tweets_over_time(screen_name).values() if d == 0])


def get_average(screen_name, mode="all"):
    """:returns: average tweets per day (mode=all) or per day with tweet output (mode=active)"""
    counter = get_tweets_over_time(screen_name)
    if mode == "all":
        return sum(counter.values()) / len(counter)
    elif mode == "active":
        return sum(counter.values()) / len([v for v in counter.values() if v > 0])
    else:
        return None
