-- img_a, img_b are 2 images. check in the database the number of rows for this pair
WITH query_vars (img_a, img_b) AS (
    VALUES (
        'wit1649_img1665_0018_96,166,538,654.jpg',
        'wit845_pdf845_16_83,1080,741,614.jpg'
    )
)
SELECT
	webapp_regionpair.img_1,
	webapp_regionpair.img_2,
	webapp_regionpair.category,
	webapp_regionpair.category_x,
	webapp_regionpair.similarity_type
FROM webapp_regionpair, query_vars
WHERE
    (
        webapp_regionpair.img_1 = img_a
        AND webapp_regionpair.img_2 = img_b
    ) OR (
        webapp_regionpair.img_1 = img_b
        AND webapp_regionpair.img_2 = img_a
    )
;
