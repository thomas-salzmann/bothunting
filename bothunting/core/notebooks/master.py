import csv
import datetime
import pathlib
import sys
from typing import Union

import pandas as pd
import sklearn
import termcolor
import tweepy
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from bothunting.core.notebooks.login_data import *

from bothunting import definitions
from bothunting.utils import pathutil
from bothunting.utils import osutil


here = pathlib.Path(__file__).resolve().parent
classifier = None


def api_setup(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
) -> tweepy.API:
    """Connect to Twitter API.

    Args:
        consumer_key (str): Consumer key.
        consumer_secret (str): Consumer secret.
        access_token (str): Access token.
        access_token_secret (str): Access token secret.

    Returns:
        tweepy.API: Connector to Twitter API.
    """
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth, wait_on_rate_limit=True)


def get_user(user_id: str, api: tweepy.API) -> Union[None, str]:
    """Get account data of Twitter user.

    Args:
        user_id ([type]): User id.
        api ([type]): Twitter API connector.

    Returns:
        Union[None, str]: Account data of user or None if the user account does not exist
            or is protected.
    """

    try:
        user_data = api.get_user(id=user_id)
        return user_data
    except:
        return None


def get_all_tweets(user_id, api):
    """:returns: list of all tweets of the passed user"""
    all_tweets = []
    try:
        new_tweets = api.user_timeline(id=user_id, count=200)
        all_tweets.extend(new_tweets)
        if len(all_tweets) > 0:
            oldest = all_tweets[-1].id - 1
            while len(new_tweets) > 0:
                new_tweets = api.user_timeline(
                    id=user_id, count=200, max_id=oldest
                )  # , tweet_mode='extended'
                all_tweets.extend(new_tweets)
                oldest = all_tweets[-1].id - 1
        return all_tweets
    except tweepy.error.TweepError:
        return None


def write_tweets_to_csv(tweets, file_name):
    """writes a csv file that contains a row for every tweet in tweets"""
    with open(f"{file_name}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "created_at", "text"])
        writer.writerows(
            [[tweet.id_str, tweet.created_at, tweet.text] for tweet in tweets]
        )  # tweet.full_text


def get_links_in_tweet(tweet_text):
    """:returns: (list of links in tweet_text, count of links in tweet_text)"""
    # print(re.search("(?P<url>https?://[^\s]+)", myString).group("url"))
    tweet_text = tweet_text.replace("https://pbs.twimg.com/", "")
    return [t for t in tweet_text.split(" ") if "http" in t], tweet_text.count(
        "http"
    )


def get_account_creation_datetime(account_object):
    """:returns: None if the account does not exist or else account's creation date"""
    if account_object is not None:
        return account_object.created_at
    return None


def get_time_of_existence(account_object):
    """:returns: None if the account does not exist or else the amount of days since the account's creation"""
    if account_object is not None:
        return (
            datetime.datetime.now()
            - get_account_creation_datetime(account_object)
        ).days
    return None


def get_tweet_distribution(tweet_list, account_object=None):
    """:returns: dictionary with all days as dates since the first tweet's creation (date='date_of_first_tweet') or the
    passed date (datetime object) as keys and the amount of tweets tweeted on that day from tweet_list
    (e.g. get_all_tweets(account_object.screen_name)) as values"""
    if tweet_list is None:
        return None
    counter = {}
    if account_object is None:
        first_date = tweet_list[0].created_at
    else:
        first_date = get_account_creation_datetime(account_object)
    first_date = datetime.date(
        year=first_date.year, month=first_date.month, day=first_date.day
    )
    today = datetime.date.today()
    for i in range(0, (today - first_date).days + 1):
        counter[first_date + datetime.timedelta(days=i)] = 0
    for tweet in tweet_list:
        date = tweet.created_at
        counter[
            datetime.date(year=date.year, month=date.month, day=date.day)
        ] += 1
    return counter


def get_inactive_days(tweet_list, account_object=None):
    """:returns: number of days since the account's creation or the first tweet's date on which was not tweeted"""
    if tweet_list is None:
        return None
    return len(
        [
            d
            for d in get_tweet_distribution(
                tweet_list=tweet_list, account_object=account_object
            ).values()
            if d == 0
        ]
    )


def get_average(tweet_list, account_object=None, mode="all"):
    """:returns: average tweets per day (mode="all") or per day with tweet output (mode="active")"""
    if tweet_list is not None:
        counter = get_tweet_distribution(
            tweet_list=tweet_list, account_object=account_object
        )
        if mode == "all":
            return sum(counter.values()) / len(counter)
        elif mode == "active":
            return sum(counter.values()) / len(
                [v for v in counter.values() if v > 0]
            )
    else:
        return None


def has_default_image(account_object):
    if account_object is None:
        return None
    elif (
        account_object.profile_image_url
        == "http://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png"
    ):
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


def is_protected(account_object):
    if account_object is None:
        return None
    if account_object.protected:
        return True
    return False


def is_verified(account_object):
    if account_object is None:
        return None
    return account_object.verified


def geo_is_enabled(account_object):
    if account_object is None:
        return None
    if account_object.geo_enabled:
        return True
    return False


def compute_row(df, user_id, api):
    print("--", user_id, "--")
    changed = False
    acc = None
    twl = None
    functions = [
        (is_protected, "is_protected", 0),
        (get_time_of_existence, "time_of_existence", 0),
        (get_average, "average_daily_tweets", 1),
        (get_inactive_days, "inactive_days", 1),
        (has_default_image, "has_default_image", 0),
        (bio_is_empty, "bio_is_empty", 0),
        (friends_followers_ratio, "friends_followers_ratio", 0),
        (is_verified, "is_verified", 0),
    ]  # TODO: ,(geo_is_enabled, "geo_is_enabled", 0)
    for f in functions:
        if pd.isnull(df[f[1]][user_id]):
            if acc is None:
                acc = get_user(user_id=user_id, api=api)
                if acc is None:
                    break
            temp = df[f[1]][user_id]
            if f[2] == 0:
                df.at[user_id, f[1]] = f[0](account_object=acc)
            elif f[2] == 1 and not df["is_protected"][user_id]:
                if twl is None:
                    twl = get_all_tweets(user_id=user_id, api=api)
                    if twl is None:
                        continue
                df.at[user_id, f[1]] = f[0](tweet_list=twl, account_object=acc)
            print(user_id, "-", f[1] + ":", temp, "->", df[f[1]][user_id])
            if temp != df[f[1]][user_id] and pd.notnull(df[f[1]][user_id]):
                changed = True
    return df, changed


def expand_rows(csv_file, api):
    df = pd.read_csv(csv_file, index_col=0)
    wrong_rows = []
    # add the columns to the dataframe
    for column_name in [
        "is_protected",
        "time_of_existence",
        "average_daily_tweets",
        "inactive_days",
        "has_default_image",
        "bio_is_empty",
        "friends_followers_ratio",
        "is_verified",
    ]:  # TODO: , "geo_is_enabled"
        if column_name not in df.columns:
            df[column_name] = None
    # print and save the amount of rows with a time_of_existence value but no average_daily_tweets value
    print(
        1,
        "-",
        len(
            df.loc[
                df["time_of_existence"].notnull()
                & df["average_daily_tweets"].isnull()
                & (df["is_protected"] != True)
            ].index
        ),
        "rows wrong",
    )
    wrong_rows.append(
        len(
            df.loc[
                df["time_of_existence"].notnull()
                & df["average_daily_tweets"].isnull()
                & (df["is_protected"] != True)
            ].index
        )
    )
    # try to expand all rows in df
    for user_id in list(df.index.values):
        (df, changed) = compute_row(df, int(user_id), api)
        if changed:
            df.to_csv(csv_file)
    # expand rows with a time_of_existence value but no average_daily_tweets value until there are no left
    i = 2
    while (
        len(
            df.loc[
                df["time_of_existence"].notnull()
                & df["average_daily_tweets"].isnull()
                & (df["is_protected"] != True)
            ].index
        )
        > 0
    ):
        print(
            i,
            "-",
            len(
                df.loc[
                    df["time_of_existence"].notnull()
                    & df["average_daily_tweets"].isnull()
                    & (df["is_protected"] != True)
                ].index
            ),
            "rows wrong",
        )
        wrong_rows.append(
            len(
                df.loc[
                    df["time_of_existence"].notnull()
                    & df["average_daily_tweets"].isnull()
                    & (df["is_protected"] != True)
                ].index
            )
        )
        for user_id in list(
            df.loc[
                df["time_of_existence"].notnull()
                & df["average_daily_tweets"].isnull()
                & (df["is_protected"] != True)
            ].index.values
        ):
            (df, changed) = compute_row(df, int(user_id), api)
            if changed:
                df.to_csv(csv_file)
        i += 1
    print(wrong_rows)


def filter_columns(df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
    df = df.copy()
    header = list(df.columns)
    idx = header.index("is_protected")
    new_header = ["id"] + header[idx:]
    if debug:
        print(f"header={header}")
        print(f"new_header={new_header}")
    return df[new_header]


def filter_removed_accounts(df: pd.DataFrame):
    df = df.copy()
    return df[~pd.isnull(df["time_of_existence"])]


def predict(classifier, fts: pd.DataFrame) -> int:
    """Predict class for feature values.

    Args:
        classifier ([type]): Classifier object.
        fts ([type]): Feature values.

    Returns:
        [type]: Possible values:

            * 0: Human.
            * 1: Traditional Bot.
            * 2: Social Bot.
    """
    # ! Applying fit_transforms() makes the feature vector equal to
    # ! an array of 0, and thus, always gives the result 'Human'.
    # fts = StandardScaler().fit_transform(fts)
    return classifier.predict(fts)


def setup_classifier(
    debug: bool = False,
) -> sklearn.ensemble.RandomForestClassifier:
    """Setup classifier.

    Returns:
        [type]: [description]
    """
    global here
    df = pd.read_csv(here / "complete_data.csv")
    df = filter_removed_accounts(filter_columns(df)).dropna()
    # df = df.loc[df["is_protected"].isnull()]
    X_header = [
        "is_protected",
        "time_of_existence",
        "average_daily_tweets",
        "inactive_days",
        "has_default_image",
        "bio_is_empty",
        "friends_followers_ratio",
        "is_verified",
    ]
    # ! Das Ergebnis df["result"] war teil von 'X'. Somit war die Güte
    # ! der Vorhersage 100%, weil das Ergebnis selbst ein Prädiktor war.
    # X_header = list(df.columns)[1:]
    X, y = df[X_header], df["result"]
    # ? Why does the prediction suddenly work when fit_transform() is
    # ? not applied
    # X = StandardScaler().fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    RFC = RandomForestClassifier()
    classifier = RFC.fit(X_train, y_train)

    if debug:
        y_pred = classifier.predict(X_test)
        report = classification_report(y_test, y_pred)
        conf_matrix = confusion_matrix(y_test, y_pred)
        print(df.shape)
        print(X_train.shape)
        print(y_train.shape)
        print(X_test.shape)
        print(y_test.shape)
        print(report)
        print(conf_matrix)

        y_pred = classifier.predict(X_train)
        report = classification_report(y_train, y_pred)
        conf_matrix = confusion_matrix(y_train, y_pred)
        print(report)
        print(conf_matrix)

    return classifier


def _get_features_and_user_id(
    username: str, api: tweepy.API, classifier
) -> pd.DataFrame:
    feature_dir = definitions.get_out_dir() / "features"
    if not pathutil.is_dir(feature_dir):
        osutil.mkdir(feature_dir)
    path_features = feature_dir / f"{username}_account_features.csv"
    if not pathutil.is_file(path_features):
        acc = api.get_user(screen_name=username)
        user_id = acc.id
        columns = [
            "is_protected",
            "time_of_existence",
            "average_daily_tweets",
            "inactive_days",
            "has_default_image",
            "bio_is_empty",
            "friends_followers_ratio",
            "is_verified",
        ]
        d = {"id": user_id}
        for c in columns:
            d[c] = [None]
        fts, changed = compute_row(
            pd.DataFrame(data=d, index=[user_id]), user_id, api
        )
        fts = fts[columns]
        fts.to_csv(path_features, index=False)
    else:
        fts = pd.read_csv(path_features)
        user_id = 0
    return fts, user_id


def classify_account(username: str, api: tweepy.API) -> str:
    """Classify Twitter account.

    Args:
        username (str): Username of account. This is the name shown on the
            screen.
        api (tweepy.api.API): Twitter API connector.

    Returns:
        str: "Human", "Traditional Bot" or "Social Bot".
    """
    global here
    global classifier
    map_ = {0: "Human", 1: "Traditional Bot", 2: "Social Bot", -1: "Error"}
    if classifier is None:
        classifier = setup_classifier(debug=True)
    try:
        fts, user_id = _get_features_and_user_id(username, api, classifier)
    except tweepy.error.TweepError:
        # Raised if user could not be found by Twitter API connector.
        return map_[-1]
    if fts["is_protected"][user_id] or fts["is_verified"][user_id]:
        print(termcolor.colored("If Clause", "red"))
        return map_[0]
    class_ = predict(classifier, fts)[0]
    return map_[class_]


def main() -> int:
    consumer_key = "2dqM1oxHL6ybNsSfMgdwGf2iO"
    consumer_secret = "sYKbwIC24d9RKtZW5CXaxK8t8Q5fMvG1hkkYtV4At9egh9Fdd4"
    access_token = "1898213802-g9kTPGb720zaVjHeA73APcn8NwsDrPjCnh9qbf6"
    access_token_secret = "8lu2Rmhzmve4GtzVvWNXVM2nZCrzA1g3BTpsIj8HvTUOf"
    api = api_setup(
        consumer_key, consumer_secret, access_token, access_token_secret
    )
    users = [
        "DanieleMaraldi",
        "GianlucaPriopi",
        "SaverioParnasse",
        "LauraNannino",
        "CarloMichettoni",
        "OriettaBenci",
        "FrancoLeone99",
        "DavideOnofi",
        "StefanoGardelli",
        "SilviaSenigalli",
        "SimoneVassala",
        "MickySavona",
        "ilovetheadlibs",
        "IDIGWEBSITES1",
        "iloveseniorgame",
        "Iloveseniorrela",
        "Iloveseniorfitn",
        "Iloveseniortech",
        "Rumphdig",
        "Lilladig",
        "Buhldig",
        "Whitforddig",
        "Featheroffdig",
        "Converydig",
        "Waeyaertdig",
        "Nixiondig",
        "KBizResources",
        "fitness0012",
        "NewToHR",
        "McGeehan_M",
        "MomSellsApps",
    ]
    for user in users:
        class_ = classify_account(user, api)
        print(f"Class of user '{user}': {class_}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
