def get_user(user_id, api):
    """:returns: None if the account does not exist or else the account data"""
    try:
        user_data = api.get_user(id=user_id)
        return user_data
    except:
        return None


def get_all_tweets(user_id, api):
    """:returns: list of all tweets of the passed user"""
    # initialize a list to hold all the tweepy Tweets
    all_tweets = []
    # make initial request for most recent tweets (200 is the maximum allowed count)
    try:
        new_tweets = api.user_timeline(id=user_id, count=200)
        # save most recent tweets
        all_tweets.extend(new_tweets)
        # save the id of the oldest tweet less one if there are tweets
        if len(all_tweets) > 0:
            oldest = all_tweets[-1].id - 1
            # keep grabbing tweets until there are no tweets left to grab
            while len(new_tweets) > 0:
                print(f"getting tweets before {oldest}")
                # all subsequent requests use the max_id param to prevent duplicates
                new_tweets = api.user_timeline(id=user_id, count=200,
                                               max_id=oldest)
                # save most recent tweets
                all_tweets.extend(new_tweets)
                # update the id of the oldest tweet less one
                oldest = all_tweets[-1].id - 1
                print(f"...{len(all_tweets)} tweets downloaded so far")
        return all_tweets
    except:
        return None
    pass


def write_tweets_to_csv(tweets, file_name):
    """writes a csv file that contains a row for every tweet in tweets"""
    with open(f'{file_name}.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "created_at", "text"])
        writer.writerows([[tweet.id_str, tweet.created_at, tweet.text] for tweet in tweets])  # tweet.full_text


def get_links_in_tweet(tweet_text):
    """:returns: (list of links in tweet_text, count of links in tweet_text)"""
    # print(re.search("(?P<url>https?://[^\s]+)", myString).group("url"))
    tweet_text = tweet_text.replace("https://pbs.twimg.com/", "")
    return [t for t in tweet_text.split(" ") if "http" in t], tweet_text.count("http")


def get_account_creation_datetime(account_object):
    """:returns: None if the account does not exist or else account's creation date"""
    if account_object is not None:
        return account_object.created_at
    return None


def get_time_of_existence(account_object):
    """:returns: None if the account does not exist or else the amount of days since the account's creation"""
    if account_object is not None:
        return (datetime.datetime.now() - get_account_creation_datetime(account_object)).days
    return None


def get_tweet_distribution(tweet_list, account_object=None):
    """:returns: dictionary with all days as dates since the first tweet's creation (date='date_of_first_tweet') or the
    passed date (datetime object) as keys and the amount of tweets tweeted on that day from tweet_list
    (e.g. get_all_tweets(account_object.screen_name)) as values"""
    if tweet_list is None:
        return None
    counter = {}
    if account_object is None:
        first_date = tweet_list[0].date
    else:
        first_date = get_account_creation_datetime(account_object)
    first_date = datetime.date(year=first_date.year, month=first_date.month, day=first_date.day)
    today = datetime.date.today()
    for i in range(0, (today - first_date).days + 1):
        counter[first_date + datetime.timedelta(days=i)] = 0
    for tweet in tweet_list:
        date = tweet.created_at
        counter[datetime.date(year=date.year, month=date.month, day=date.day)] += 1
    return counter


def get_inactive_days(tweet_list, account_object=None):
    """:returns: number of days since the account's creation or the first tweet's date on which was not tweeted"""
    if tweet_list is None:
        return None
    return len(
        [d for d in get_tweet_distribution(tweet_list=tweet_list, account_object=account_object).values() if d == 0])


def get_average(tweet_list, account_object=None, mode="all"):
    """:returns: average tweets per day (mode="all") or per day with tweet output (mode="active")"""
    if tweet_list is not None:
        counter = get_tweet_distribution(tweet_list=tweet_list, account_object=account_object)
        if mode == "all":
            return sum(counter.values()) / len(counter)
        elif mode == "active":
            return sum(counter.values()) / len([v for v in counter.values() if v > 0])
    else:
        return None


def has_default_image(account_object):
    if account_object is None:
        return None
    elif account_object.profile_image_url == "http://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png":
        return True
    else:
        return False


def bio_is_empty(account_object):
    if account_object is None:
        return None
    elif account_object.description == "":
        return True
    else:
        return False


def friends_followers_ratio(account_object):
    if account_object is None:
        return None
    follower = account_object.followers_count
    friends = account_object.friends_count
    try:
        return friends / follower
    except ZeroDivisionError:
        return None


def is_verified(account_object):
    if account_object is None:
        return None
    return account_object.verified


def expand_dataset(csv_file, api):
    df = pd.read_csv(csv_file)
    functions = [(get_time_of_existence, "time_of_existence", 0), (get_average, "average_daily_tweets", 1),
                 (get_inactive_days, "inactive_days", 1), (has_default_image, "has_default_image", 0),
                 (bio_is_empty, "bio_is_empty", 0), (friends_followers_ratio, "friends_followers_ratio", 0),
                 (is_verified, "is_verified", 0)]
    accounts = []
    tweets = []
    for user_id in df["id"]:
        accounts.append(get_user(user_id, api))
        tweets.append(get_all_tweets(user_id, api))
    print(df.info(), len(accounts), len(tweets))
    for f in functions:
        res = []
        for i in range(len(accounts)):
            if accounts[i] is None:
                res.append(None)
            else:
                if f[2] == 0:
                    res.append(f[0](account_object=accounts[i]))
                if f[2] == 1:
                    res.append(f[0](tweet_list=tweets[i], account_object=accounts[i]))
        df[f[1]] = res
        df.to_csv(csv_file, index=False)