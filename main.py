from dataclasses import dataclass, field

@dataclass(frozen=True)
class Movie:
    title: str

@dataclass
class Genre:
    name: str
    keywords: list[str]
    movies: list[Movie] = field(default_factory=list)

    def matches(self, text: str) -> bool:
        """사용자 메시지 text에 이 장르를 나타내는 키워드가 포함되어 있는지 확인합니다."""
        return any(keyword in text.lower() for keyword in self.keywords)

    def movies_in_text(self, text: str) -> list[Movie]:
        """사용자 메시지 text 언급된, 이 장르 소속 영화를 찾습니다."""
        return [movie for movie in self.movies if movie.title in text]

    def unwatched_movies(self, watched: set[str]) -> list[Movie]:
        """아직 보지 않은 영화만 필터링합니다."""
        return [movie for movie in self.movies if movie.title not in watched]


class MovieCatalog:
    """모든 장르와 영화 데이터를 관리하고 검색·추천 로직을 제공하는 카탈로그."""

    def __init__(self, genres: list[Genre]):
        self.genres = genres

    def find_genre(self, text: str) -> Genre | None:
        """사용자 메시지 text에서 언급된 장르를 찾습니다"""
        for genre in self.genres:
            if genre.matches(text):
                return genre
        return None

    def find_watched_movies(self, text: str) -> list[str]:
        """사용자 메시지 text에서 이미 본 것으로 언급된 영화 제목을 찾습니다"""
        found: list[str] = []
        for genre in self.genres:
            for movie in genre.movies_in_text(text):
                if movie.title not in found:
                    found.append(movie.title)
        return found

    def recommend(
        self,
        favorite_genres: list[Genre],
        watched_movies: list[str],
        limit: int = 3,
    ) -> list[str]:
        """선호 장르 기준으로 아직 보지 않은 영화를 추천합니다"""
        watched = set(watched_movies)
        candidates: list[str] = []

        for genre in favorite_genres:
            for movie in genre.unwatched_movies(watched):
                if movie.title not in candidates:
                    candidates.append(movie.title)

        return candidates[:limit]


def create_default_catalog() -> MovieCatalog:
    """SF, 액션, 로맨스, 공포, 드라마 장르가 포함된 기본 영화 카탈로그를 생성합니다"""
    return MovieCatalog(
        [
            Genre(
                "SF",
                ["sf", "공상과학", "sci-fi", "science fiction"],
                [
                    Movie("인셉션"),
                    Movie("인터스텔라"),
                    Movie("매트릭스"),
                    Movie("블레이드 러너 2049"),
                    Movie("어라이벌"),
                    Movie("엑스 마키나"),
                    Movie("마션"),
                    Movie("그래비티"),
                ],
            ),
            Genre(
                "액션",
                ["액션", "action"],
                [
                    Movie("다크 나이트"),
                    Movie("존 윅"),
                    Movie("미션 임파서블"),
                    Movie("어벤져스"),
                    Movie("매드맥스: 분노의 도로"),
                ],
            ),
            Genre(
                "로맨스",
                ["로맨스", "멜로", "romance"],
                [
                    Movie("라라랜드"),
                    Movie("어바웃 타임"),
                    Movie("노트북"),
                    Movie("비포 선라이즈"),
                    Movie("타이타닉"),
                ],
            ),
            Genre(
                "공포",
                ["공포", "호러", "좀비", "귀신", "horror", "scary", "thrilling"],
                [
                    Movie("겟 아웃"),
                    Movie("헤어질 결심"),
                    Movie("컨저링"),
                    Movie("쏘우"),
                    Movie("라이트 아웃"),
                ],
            ),
            Genre(
                "드라마",
                ["드라마", "drama"],
                [
                    Movie("쇼생크 탈출"),
                    Movie("포레스트 검프"),
                    Movie("기생충"),
                    Movie("녹색 빛"),
                    Movie("위대한 쇼맨"),
                ],
            ),
        ]
    )


class MovieRecommendationBot:
    """대화 기록과 메모리를 활용하는 영화 추천 챗봇"""

    def __init__(self):
        self.catalog = create_default_catalog()
        self.messages: list[dict[str, str]] = []
        self.favorite_genres: list[Genre] = []
        self.watched_movies: list[str] = []

    def append_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def remember_genre(self, genre: Genre):
        if genre not in self.favorite_genres:
            self.favorite_genres.append(genre)

    def remember_watched(self, movies: list[str]):
        for movie in movies:
            if movie not in self.watched_movies:
                self.watched_movies.append(movie)

    def expresses_genre_preference(self, text: str) -> bool:
        """사용자 메시지가 장르에 대한 호감을 표현하는지 판별합니다."""
        keywords = ["좋아해", "좋아해요", "좋아하는", "좋아하", "좋아"]
        return any(keyword in text for keyword in keywords)

    def expresses_watched_movie(self, text: str) -> bool:
        """사용자 메시지가 영화를 이미 봤다고 표현하는지 판별합니다."""
        keywords = ["이미 봤어", "이미 봤어요", "봤어요", "봤어", "봤습니다", "봤", "본"]
        return any(keyword in text for keyword in keywords)

    def get_recommendations(self, limit: int = 3) -> list[str]:
        return self.catalog.recommend(self.favorite_genres, self.watched_movies, limit)

    def format_movie_list(self, movies: list[str]) -> str:
        if len(movies) == 1:
            return movies[0]
        if len(movies) == 2:
            return f"{movies[0]}과 {movies[1]}"
        return ", ".join(movies[:-1]) + f"과 {movies[-1]}"

    def generate_response(self, user_message: str) -> str:
        genre = self.catalog.find_genre(user_message)
        watched = self.catalog.find_watched_movies(user_message)
        likes_genre = genre and self.expresses_genre_preference(user_message)
        has_watched = watched and self.expresses_watched_movie(user_message)

        if likes_genre:
            self.remember_genre(genre)

        if has_watched:
            self.remember_watched(watched)

        if self.is_recall_question(user_message):
            return self.build_recall_response()

        if self.is_recommendation_request(user_message):
            return self.build_recommendation_response()

        if likes_genre:
            return f"좋은 취향이시네요! {genre.name}에는 명작이 정말 많죠. 취향에 맞는 영화를 골라드릴게요."

        if has_watched:
            movie_text = self.format_movie_list(watched)
            return f"좋은 선택이셨네요! {movie_text}는 이미 보셨으니까 비슷한 취향이면 다른 작품도 추천해 드릴 수 있어요."

        return "알겠습니다! 좋아하는 장르나 이미 본 영화를 알려주시면 맞춤 추천을 해 드릴게요."

    def is_recommendation_request(self, text: str) -> bool:
        """사용자가 영화 추천을 요청하는 메시지인지 판별합니다"""
        keywords = ["추천", "뭐 볼", "볼까", "볼지", "추천해"]
        return any(keyword in text for keyword in keywords)

    def is_recall_question(self, text: str) -> bool:
        """사용자가 이전에 말한 취향·시청 기록을 묻는 메시지인지 판별합니다"""
        keywords = ["뭐라고 했", "뭐였", "기억", "알려줘", "뭐였지", "뭐라고 했지"]
        return any(keyword in text for keyword in keywords) and (
            "장르" in text or "영화" in text or "봤" in text
        )

    def build_recommendation_response(self) -> str:
        """저장된 취향과 시청 기록을 반영한 추천 응답 문장을 생성합니다"""
        recommendations = self.get_recommendations()
        genre_names = [genre.name for genre in self.favorite_genres]
        genre_text = self.format_movie_list(genre_names) if genre_names else "다양한 장르"
        watched_text = (
            self.format_movie_list(self.watched_movies)
            if self.watched_movies
            else None
        )

        if not recommendations:
            if watched_text is not None:
                return (
                    f"{genre_text}를 좋아하시고, {watched_text}는 이미 보셨으나 "
                    "지금은 새로 추천할 만한 작품이 떠오르지 않네요. 다른 장르를 알려주시면 다시 찾아볼게요!"
                )
            return (
                f"{genre_text}를 좋아하시니까 추천드리고 싶은데, "
                "지금은 새로 추천할 만한 작품이 떠오르지 않네요. 다른 장르를 알려주시면 다시 찾아볼게요!"
            )

        rec_text = ", ".join(recommendations)
        if watched_text is not None:
            return (
                f"{genre_text}를 좋아하시고, {watched_text}는 이미 보셨으니까 추천드리자면 "
                f"{rec_text} 어떠세요? 오늘 밤에 보기 좋은 작품들이에요!"
            )
        return (
            f"{genre_text}를 좋아하시니까 추천드리자면 "
            f"{rec_text} 어떠세요? 오늘 밤에 보기 좋은 작품들이에요!"
        )

    def build_recall_response(self) -> str:
        """저장된 선호 장르와 시청 영화를 되짚어 주는 응답 문장을 생성합니다.

        Returns:
            기억하고 있는 장르·영화 정보를 요약한 응답.
            저장된 정보가 없으면 안내 메시지를 반환합니다.
        """
        has_favorite_genres = bool(self.favorite_genres)
        has_watched = bool(self.watched_movies)

        if not has_favorite_genres and not has_watched:
            return "아직 좋아하는 장르나 본 영화에 대해 말씀해 주신 내용이 없어요."

        genre_text = (
            self.format_movie_list([genre.name for genre in self.favorite_genres])
            if has_favorite_genres
            else None
        )
        watched_text = (
            self.format_movie_list(self.watched_movies)
            if has_watched
            else None
        )

        if has_favorite_genres and not has_watched:
            return (
                f"{genre_text}를 좋아하신다고 했죠. "
                "아직 본 영화에 대해서는 말씀해 주신 내용이 없어요."
            )

        if has_watched and not has_favorite_genres:
            return (
                f"{watched_text}를 보셨습니다. "
                "아직 좋아하는 장르에 대해서는 말씀해 주신 내용이 없어요."
            )

        return f"{genre_text}를 좋아하신다고 했죠! {watched_text}를 보셨습니다."

    def chat(self, user_message: str) -> str:
        """사용자 메시지를 받아 응답을 생성하고 대화 기록에 저장합니다.

        user 메시지와 assistant 응답을 messages에 순서대로 append합니다.

        """
        self.append_message("user", user_message)
        assistant_message = self.generate_response(user_message)
        self.append_message("assistant", assistant_message)
        return assistant_message



MyMovieRecommendationBot = MovieRecommendationBot()

test_conversation = [
    "나는 SF 영화를 좋아해",
    "인셉션이랑 인터스텔라는 이미 봤어",
    "오늘 밤에 뭐 볼지 추천해 줄래?",
    "내가 좋아하는 장르랑 이미 본 영화가 뭐라고 했지?",
]

# 대화 출력
for user_message in test_conversation:
    response = MyMovieRecommendationBot.chat(user_message)
    print(f"User: {user_message}")
    print(f"AI: {response}\n")

# 저장된 메모리
for message in MyMovieRecommendationBot.messages:
    print(message)

# 메모리 상태 확인
print("좋아하는 장르:", [genre.name for genre in MyMovieRecommendationBot.favorite_genres])
print("이미 본 영화:", MyMovieRecommendationBot.watched_movies)
print("추천 가능한 SF 영화:", MyMovieRecommendationBot.get_recommendations())